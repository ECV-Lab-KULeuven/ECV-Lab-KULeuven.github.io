#!/bin/bash -l

#SBATCH --time 5-00:00:00
#SBATCH --gres="gpu:1"
#SBATCH --partition=batch
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=10240 # 10GB
#SBATCH --signal=B:USR1@1800  # Send SIGUSR1 30x60 seconds before walltime expires
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=bram.vrancken@ulb.be

module load beagle-lib/4.0.1-GCC-12.3.0-CUDA-12.1.1
module load Python/3.11.3-GCCcore-12.3.0

export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

# ==============================================================================
# USAGE INSTRUCTIONS
# ==============================================================================
# To submit a job:
#   XML=your_analysis.xml
#   sbatch --export=XML=$XML,WD=`pwd` --output=${XML%%.xml}.o --error=${XML%%.xml}.e --job-name=${XML%%.xml} lyra.beast.gpu.iterative.slurm
# ==============================================================================

# ==============================================================================
# CONFIGURATION - User-configurable parameters
# ==============================================================================
MAX_ITERATIONS=5                    # Maximum number of iterations (5-day runs)
INSTANCE=1                          # GPU instance to use
saveEveryState=1000000              # BEAST saves state every N MCMC iterations
beast_version="beast.10.5.0.jar"    # BEAST version to use
minimum_required_ESS=200            # Adjust as you see fit

# ==============================================================================
# SCRIPT BEHAVIOR
# ==============================================================================
# This script runs BEAST iteratively until convergence or MAX_ITERATIONS:
#
# 1. BEAST runs for duration specified by --time (or until MCMC completes)
# 2. After BEAST stops (for ANY reason except errors):
#    - ESS values are checked using check_beast_ess.py
#    - If all ESS > minimum_required_ESS: DONE (no more iterations)
#    - If any ESS < minimum_required_ESS: submit next iteration
#    - If MAX_ITERATIONS reached: stop (even if ESS insufficient)
#
# 3. ESS checking happens whether BEAST:
#    - Completed all MCMC iterations naturally, OR
#    - Was stopped by walltime signal (SIGUSR1)
#
# 4. Each iteration resumes from the previous checkpoint file
#    (periodic state saves at intervals defined by saveEveryState)
#
# Note: Only errors (exit code ≠ 0) prevent ESS checking and iteration.

# ==============================================================================
# ITERATION TRACKING
# ==============================================================================
# Initialize iteration counter if not set (passed via --export)
START_COUNTER=1
if [ -z "$ITERATION" ]; then
    ITERATION="$START_COUNTER"
fi

# ==============================================================================
# INTERNAL STATE - Do not modify
# ==============================================================================
BEAST_PID=""                  # Will store PID of running BEAST process
RECEIVED_SIGNAL=false         # Flag set when SLURM sends termination signal

# ==============================================================================
# FUNCTION DEFINITIONS
# ==============================================================================

# Signal handler for BEAST shutdown
# This is called when SLURM sends SIGUSR1 (before walltime expires)
# NOTE: BEAST saves state at pre-specified regular intervals defined by 
# variable saveEveryState (see above). We rely on the most recent periodic 
# saved state.
sig_handler() {
    echo
    echo "=================================================================================="
    echo "Received signal from SLURM: walltime approaching."
    echo "Stopping BEAST to allow ESS checking and job resubmission"
    echo "when not all ESS values > user-specified threshold (minimum_required_ESS)..."
    echo "=================================================================================="
    RECEIVED_SIGNAL=true
    
    # check we have a PID value before trying to use it, and 
    # also check if the process $BEAST_PID actually exists
    # (2>/dev/null suppresses error messages)
    if [ ! -z "$BEAST_PID" ] && kill -0 $BEAST_PID 2>/dev/null; then
        echo "Sending SIGTERM to BEAST (PID: $BEAST_PID)"
        kill -TERM $BEAST_PID # Sends signal to the Java/BEAST process, not the script
        wait $BEAST_PID
        echo "BEAST stopped."
    fi
}

# Register the signal handler (stays active for entire script lifetime)
trap 'sig_handler' USR1


# ==============================================================================
# MAIN LOGIC
# ==============================================================================

echo
echo "=================================================================================="
echo "BEAST Iterative Run - Iteration $ITERATION of $MAX_ITERATIONS"
echo "=================================================================================="
cd $WD
echo "Current working dir: $WD"
echo


# Store the original XML base name (remove any .iterN and .xml suffixes)
if [ -z "$ORIGINAL_XML_BASENAME" ]; then
    # Remove any ".iter..." suffix (if present), then strip .xml
    ORIGINAL_XML_BASENAME="${XML%%.iter*}"
    ORIGINAL_XML_BASENAME="${ORIGINAL_XML_BASENAME%%.xml}"
fi
XMLbaseName="$ORIGINAL_XML_BASENAME"

# Determine dump file names based on iteration
if [ $ITERATION -eq "$START_COUNTER" ]; then
    # First run - no previous dump file
    dumpFile=${XMLbaseName}.iter${ITERATION}.chkpt
    echo "Starting fresh run (iteration $ITERATION)"
    echo "Will save state to: $dumpFile"
    echo
    # Run BEAST in background so we can catch signals
    java -jar $HOME/biosoft/${beast_version} -citations_off \
    -beagle_gpu -beagle_order $INSTANCE -overwrite -save_every ${saveEveryState} \
    -save_state ${dumpFile} $XML &      # <- The & runs this in background
    BEAST_PID=$!                        # <- $! captures PID of that backgrounded process
else

    # Prepare new XML for this iteration to avoid overwriting existing log/trees files
    newXML=${XMLbaseName}.iter${ITERATION}.xml
    newLogFile=${XMLbaseName}.iter${ITERATION}.log
    newTreeFile=${XMLbaseName}.iter${ITERATION}.trees

    # Always copy from the original base name and previous iteration
    prevIteration=$((ITERATION - 1))
    if [ $ITERATION -eq $((START_COUNTER + 1)) ]; then
        cp "${XMLbaseName}.xml" "$newXML" #"${XMLbaseName}.iter${ITERATION}.xml"
    else
        cp "${XMLbaseName}.iter${prevIteration}.xml" "$newXML" #"${XMLbaseName}.iter${ITERATION}.xml"
    fi

    # Update log file name in the new XML
    sed -i.bak '/<log id="fileLog"/ s/\(fileName="\)[^\"]*\(".*\)/\1'"${newLogFile}"'\2/' "$newXML"
    rm -f "${newXML}.bak"
    # Update trees file name in the new XML
    sed -i.bak '/<logTree id="treeFileLog"/ s/\(fileName="\)[^\"]*\(".*\)/\1'"${newTreeFile}"'\2/' "$newXML"
    rm -f "${newXML}.bak"

    # Use the new XML for this run
    XML="$newXML"

    # Continue from previous run
    dumpFileOld=${XMLbaseName}.iter${prevIteration}.chkpt
    dumpFile=${XMLbaseName}.iter${ITERATION}.chkpt
    echo "Continuing from previous run (iteration $prevIteration)"
    echo "Loading state from: $dumpFileOld"
    echo "Will save state to: $dumpFile"
    echo
    # Run BEAST in background so we can catch signals
    java -jar $HOME/biosoft/${beast_version} -citations_off \
    -beagle_gpu -beagle_order $INSTANCE -overwrite -save_every ${saveEveryState} \
    -save_state ${dumpFile} -load_state ${dumpFileOld} $XML &
    BEAST_PID=$!
fi

echo "XML that'll be used: $XML"
echo
echo "BEAST running with PID: $BEAST_PID"

wait $BEAST_PID    #  Wait for BEAST to complete or be stopped by signal
BEAST_EXIT_CODE=$? #  Immediately capture exit code of last executed command

echo
if [ "$RECEIVED_SIGNAL" = true ]; then
    #echo "BEAST run stopped due to approaching walltime"
    echo "Last checkpoint state saved in: $dumpFile"
elif [ $BEAST_EXIT_CODE -ne 0 ]; then
    echo "ERROR: BEAST exited with error code: $BEAST_EXIT_CODE"
    echo "Check the output above for error messages"
    exit 1
else
    echo "BEAST completed successfully"
fi

echo
echo "BEAST run completed for iteration $ITERATION"
echo

# After BEAST completes, check ESS values
echo "=================================================================================="
echo "Checking ESS values..."
echo "=================================================================================="

# NOTE: This script requires check_beast_ess.py to be available in $HOME/biosoft/
# to calculate ESS values from a BEAST log file

# Activate Python virtual environment for ESS checking
if [ -f "$HOME/venv_beast/bin/activate" ]; then
    source $HOME/venv_beast/bin/activate
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to activate Python virtual environment at $HOME/venv_beast"
        echo "Please check the virtual environment setup"
        exit 1 # return exit code 1 to SLURM. this marks the job status as FAILED.
    fi
else
    echo "ERROR: Python virtual environment not found at $HOME/venv_beast/bin/activate"
    echo "Please create the virtual environment with arviz installed."
    exit 1 # return exit code 1 to SLURM. This marks the job status as FAILED.
fi

# Check if ESS checker script exists
if [ ! -f "$HOME/biosoft/check_beast_ess.py" ]; then
    echo "ERROR: ESS checker script not found."
    echo "Please ensure check_beast_ess.py is installed in $HOME/biosoft/"
    exit 1 # return exit code 1 to SLURM. This marks the job status as FAILED.
fi

# Verify arviz is available in the virtual environment
if ! python -c "import warnings; warnings.filterwarnings('ignore', category=FutureWarning); import arviz" 2>/dev/null; then
    echo "ERROR: arviz not found in virtual environment"
    echo "Please install arviz in the virtual environment:"
    exit 1
fi


#logFileBaseName="${XML%.iter[0-9]*.xml}"
#logFileBaseName="${logFileBaseName%.xml}"
logFileBaseName="$XMLbaseName"

# Find all log files matching the base name (e.g., test.r1*.log)
logFiles=( $(ls | grep "^${logFileBaseName}.*\\.log$") )

if [ ${#logFiles[@]} -eq 0 ]; then
    echo "ERROR: No log files found matching: ${logFileBaseName}*.log"
    echo "Cannot check ESS values. Stopping."
    exit 1
fi

echo "Using log files: ${logFiles[@]}"
echo

# Run the ESS check using the standalone script
# Exit codes:   0 = success (ESS > minimum_required_ESS)
#               1 = continue needed (ESS < minimum_required_ESS)
#               2 = corrupted file
echo python $HOME/biosoft/check_beast_ess.py "$logFileBaseName" "$minimum_required_ESS"
python $HOME/biosoft/check_beast_ess.py "$logFileBaseName" "$minimum_required_ESS"
ESS_CHECK=$?

echo
echo "=================================================================================="

if [ $ESS_CHECK -eq 2 ]; then
    echo "FATAL ERROR: Log file is corrupted or incomplete."
    echo "BEAST run may have crashed or been interrupted."
    echo "Stopping all iterations. Please investigate the issue."
    echo "Total iterations completed before error: $((ITERATION + 1))"
    echo "=================================================================================="
    exit 1
elif [ $ESS_CHECK -eq 0 ]; then
    echo "All ESS values are satisfactory (>200). Analysis complete!"
    echo "Total iterations run: $((ITERATION + 1))"
    echo "=================================================================================="
    exit 0
else
    # Check if we've reached max iterations
    if [ $ITERATION -ge $((MAX_ITERATIONS - 1)) ]; then
        echo "WARNING: Maximum iterations ($MAX_ITERATIONS) reached."
        echo "ESS values are still below threshold but stopping as per limit."
        echo "Consider running additional iterations."
        echo "=================================================================================="
        exit 0
    else
        # Submit next iteration
        NEXT_ITERATION=$((ITERATION + 1))
        echo "Some ESS values are below threshold. Submitting iteration $NEXT_ITERATION..."
        echo "=================================================================================="
        echo
        
        # Submit the next job with dependency on this one
        # Export the original (non-iter) XML so the next job derives names correctly
        submit_XML="${ORIGINAL_XML_BASENAME}.xml"
        if [ -n "${SLURM_JOB_ID:-}" ]; then
            dep="--dependency=afterany:${SLURM_JOB_ID}"
        else
            dep=""
            echo "Warning: SLURM_JOB_ID not set; submitting without dependency"
        fi

        NEXT_JOB=$(sbatch $dep --export=XML=${submit_XML},WD=$WD,ITERATION=$NEXT_ITERATION \
                          --output=${XMLbaseName}.iter${NEXT_ITERATION}.o \
                          --error=${XMLbaseName}.iter${NEXT_ITERATION}.e \
                          --job-name=${XMLbaseName}.iter${NEXT_ITERATION} \
                          ${WD}/lyra.beast.gpu.iterative.slurm)

        echo "Submitted next iteration as job: $NEXT_JOB"
        echo "It will start after this job completes."
        echo "XML file that'll be used for this new round: ${XMLbaseName}.iter${NEXT_ITERATION}.xml (submitted as ${submit_XML})"
        # ----------------------------------------------------------------------
        # --> the use of $submit_XML can eb confusing. The point is that the next 
        # job receives that canonical XML (i.e. $submit_XML) and recomputes 
        # the iteration filename from it, which is the actual XML that'll be used
        # by BEAST in this next round (i.e. ${XMLbaseName}.iter${NEXT_ITERATION}.xml).
        # This is why both values (export vs. actual file) are printed to screen.
        # ----------------------------------------------------------------------
        exit 0
    fi
fi

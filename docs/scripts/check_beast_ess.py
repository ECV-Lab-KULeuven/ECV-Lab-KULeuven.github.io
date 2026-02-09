#!/usr/bin/env python3
"""
BEAST ESS Checker using ArviZ

This script checks if all Effective Sample Size (ESS) values in a BEAST log file
are above a specified threshold. It uses the ArviZ library for ESS calculations.

NOTE: This script automatically excludes parameters containing 'monophyly', 'age', 
or 'tmrca' in their names, as these are typically summary statistics rather
than model parameters.

The exclusion uses word boundary matching, so:
  - Excluded: 'age.root', 'age(root)', 'root.age'
  - Not excluded: 'average', 'lineage', 'rootAge' (keywords within larger words)
  
Special cases (partition-aware exclusion):
  - 'branchRates' exact OR as partition suffix (partition1.branchRates excluded, 
    but branchRates.rate or partition.branchRates.scale NOT excluded)
  - 'rootHeight' exact OR as partition suffix (partition1.rootHeight excluded,
    but rootHeight.mean NOT excluded)
  - 'treeLength' exact OR as partition suffix (partition1.treeLength excluded,
    but treeLength.mean NOT excluded)
  - 'meanRate' exact OR as partition suffix (partition1.meanRate excluded,
    but meanRate.scaled NOT excluded)
  - 'coefficientOfVariation' exact OR as partition suffix (gag.coefficientOfVariation excluded,
    but coefficientOfVariation.normalized NOT excluded)
  - 'covariance' exact OR as partition suffix (pol.covariance excluded,
    but covariance.matrix NOT excluded)
  - 'skygrid.cutOff' exact OR as partition suffix (partition1.skygrid.cutOff excluded)

Although treeLikelihoods also are not parameters of the model, they are kept for 
ESS checking now (it is presumed that having their ESS > 200 is still useful
information).

Usage:
    python check_beast_ess.py <log_file> [min_ess]

Arguments:
    log_file  : Path to BEAST .log file
    min_ess   : Minimum ESS threshold (default: 200)

Exit codes:
    0 : All ESS values are above threshold
    1 : Some ESS values are below threshold
    2 : Log file is corrupted or incomplete (rows with missing data)

If you use ArviZ in your scientific work, consider citing it using 
https://doi.org/10.21105/joss.01143

Author: Bram Vrancken
Date: February 2026
"""

import sys
import warnings
# Suppress FutureWarning from arviz about upcoming refactoring
warnings.filterwarnings('ignore', category=FutureWarning)

import glob
import arviz as az
import numpy as np
import pandas as pd
import re
import os

# ---------------------------------------------------------------------------
# Below: funtions for use within this module only (precompiled exclusion 
# patterns and helper functions). Following Python naming convention, 
# these names are prefixed with a single underscore. This is made more 
# explicit in the `__all__` below for exported symbols.
# ---------------------------------------------------------------------------
# Keywords to exclude from ESS checking (metadata, not model parameters)
EXCLUDED_KEYWORDS = ['monophyly', 'age', 'tmrca',
                     'meanRate', 'coefficientOfVariation', 'covariance',
                     'skygrid.cutOff', 'branchRates', 'rootHeight', 'treeLength']

# Partition-aware keywords (lowercase) that match either exact or partition.suffix
_PARTITION_KEYWORDS = {
    'branchrates', 'rootheight', 'treelength',
    'meanrate', 'coefficientofvariation', 'covariance', 'skygrid.cutoff'
}

def _make_patterns(keywords):
    """Precompile regex patterns for exclusion matching."""
    pats = {}
    for kw in keywords:
        kl = kw.lower()
        if kl in _PARTITION_KEYWORDS:
            # exact match OR partition.keyword (but not keyword.something)
            pats[kl] = re.compile(r'(^' + re.escape(kl) + r'$|^[^.]+\.' + re.escape(kl) + r'$)')
        else:
            # word boundary match allowing ., _, (), - separators
            pats[kl] = re.compile(r'(^|[._()-])' + re.escape(kl) + r'($|[._()-])')
    return pats

# Precompute patterns once at import time for efficiency
_EXCLUDE_PATTERNS = _make_patterns(EXCLUDED_KEYWORDS)

def _should_exclude(param_name):
    """Return True if `param_name` matches any exclusion pattern.

    This helper is module-private (leading underscore) so it is simple to
    unit-test and re-used across calls without recompiling regexes.
    """
    pl = param_name.lower()
    for _, pat in _EXCLUDE_PATTERNS.items():
        if pat.search(pl):
            return True
    return False

# Symbols starting with an underscore are considered implementation details 
# and are not exported by default.
__all__ = ['merge_beast_logfiles', 'check_ess_from_log', 'main']

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------


def merge_beast_logfiles(logFileBaseName, merged_logfile='merged.log'):
    # 1. Find all log files matching the pattern
    matches = glob.glob(f"{logFileBaseName}*.log")

    # Keep the logfiles in the order they were generated. This is done by 
    # ordering matches by the iteration marker in the filename: 
    # absence = first file, 'iter2' -> second, 'iter3' -> third, etc. 
    # Keep stable ordering otherwise.
    def _iter_index(path):
        bn = os.path.basename(path)
        m = re.search(r'iter(\d+)', bn)
        return int(m.group(1)) if m else 1

    matches_sorted = sorted(matches, key=_iter_index)

    # If glob found nothing at all, fail fast
    if not matches_sorted:
        raise FileNotFoundError(f"No log files found for base name: {logFileBaseName}")

    # Partition matches into readable regular files and unreadable/non-regular ones
    readable = [p for p in matches_sorted if os.path.isfile(p) and os.access(p, os.R_OK)]
    unreadable = [p for p in matches_sorted if p not in readable]
    if unreadable:
        print(f"ERROR: Found {len(unreadable)} unreadable or non-regular log file(s):", file=sys.stderr)
        for p in unreadable:
            print(f"  - {p}", file=sys.stderr)
        print("Aborting due to unreadable log files.", file=sys.stderr)
        sys.exit(2)

    # Now use the readable files only
    logfiles = readable
    # Avoid merging a previously merged file if it exists
    if merged_logfile in logfiles:
        logfiles.remove(merged_logfile)
        print(f"\nNote: Found existing merged log file '{merged_logfile}' and will exclude it from merging.\n")
    if not logfiles:
        raise FileNotFoundError(f"No log files found to merge after excluding '{merged_logfile}'.")

    # 2. Read and concatenate all log files, skipping duplicate headers
    dfs = []
    for fname in logfiles:
        print(f"Reading log file: {fname}")
        with open(fname) as f:
            # Find the header line (skip comments)
            for line in f:
                if not line.startswith('#'):
                    header = line.strip().split('\t')
                    break
            # Read the rest as DataFrame
        df = pd.read_csv(fname, sep='\t', comment='#', header=0)
        dfs.append(df)
    # concatenate (preserve order of dfs)    
    merged = pd.concat(dfs, ignore_index=True, sort=False)
    # Next run starts from the previous run's checkpoint, so the last lines of 
    # one file may be duplicated as the first lines of the next.   
    # Prefer the last occurrence of each 'state' (later file) but be robust:
    if 'state' in merged.columns:
        merged['state'] = pd.to_numeric(merged['state'], errors='coerce')
        merged = merged.dropna(subset=['state'])
        merged = merged.drop_duplicates(subset='state', keep='last')
    else:
        # fallback: drop exact duplicate rows
        merged = merged.drop_duplicates(keep='first')
    
    # 3. Sort by 'state'
    merged = merged.sort_values(by='state')
    # Print summary information about the merged state range for user visibility
    if 'state' in merged.columns and not merged['state'].isna().all():
        try:
            min_state = int(merged['state'].min())
            max_state = int(merged['state'].max())
        except Exception:
            min_state = merged['state'].min()
            max_state = merged['state'].max()
        print(f"\nMerged log states: {min_state} .. {max_state} (rows={len(merged)})\n")
    else:
        print(f"\nMerged log: no valid 'state' column found; rows={len(merged)}\n")
    # 4. Write merged file (with header and comments from the first file)
    with open(logfiles[0]) as f:
        comments = [line for line in f if line.startswith('#')]
    with open(merged_logfile, 'w') as out:
        out.writelines(comments)
        merged.to_csv(out, sep='\t', index=False)

    return merged_logfile


def check_ess_from_log(log_file, min_ess, burnin_fraction):
    """Check if all ESS values in BEAST log are above threshold.
    
    Excludes summary statistics.
    
    Also excludes exact matches only: 'branchRates', 'meanRate', 
    'coefficientOfVariation', 'covariance', 'skygrid.cutOff', 'rootHeight', 
    'treeLength' (derived parameters like 'branchRates.variance' are NOT excluded).
    
    Args:
        log_file: Path to BEAST log file
        min_ess: Minimum ESS threshold (default: 200)
    
    Returns:
        tuple: (all_above_threshold, min_ess_value, param_with_min_ess)
    """
    # Use module-private helper _should_exclude (precompiled patterns)
    # to decide whether a header should be skipped from ESS calculations.
    
    try:
        # Read BEAST log file
        # Skip comment lines and read the data
        data = []
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                data.append(line)
        
        if len(data) < 2:
            print(f"Error: Log file appears empty or invalid", file=sys.stderr)
            return False, 0, "unknown"
        
        # First non-comment line is header
        headers = data[0].split('\t')
        
        # Build values dictionary, excluding metadata parameters
        values = {}
        excluded_params = []
        for header in headers:
            # Skip state/sample columns
            if header in ['state', 'Sample']:
                continue
            # Exclude parameters containing metadata keywords (word boundary matching)
            if _should_exclude(header):
                excluded_params.append(header)
                continue
            values[header] = []
        
        if excluded_params:
            print(f"  Excluding {len(excluded_params)} metadata parameters:", file=sys.stderr)
            for param in excluded_params:
                print(f"    - {param}", file=sys.stderr)
        
        total_rows = len(data) - 1  # Exclude header
        
        # Parse numeric data rows
        states = []
        for row_num, line in enumerate(data[1:], start=2):  # Start at 2 (line 1 is header)
            parts = line.split('\t')
            if len(parts) != len(headers):
                # Even a single incomplete row indicates a problem
                print(f"\nERROR: Incomplete row detected at line {row_num}", file=sys.stderr)
                print(f"ERROR: Expected {len(headers)} columns, found {len(parts)}", file=sys.stderr)
                print(f"ERROR: Log file is corrupted or incomplete. This may indicate:", file=sys.stderr)
                print(f"  - BEAST run crashed or was interrupted", file=sys.stderr)
                print(f"  - Disk full error during writing", file=sys.stderr)
                print(f"  - File corruption", file=sys.stderr)
                print(f"\nStopping analysis. Please investigate the log file.", file=sys.stderr)
                return False, 0, "corrupted_file"
            
            state_val = float(parts[headers.index('state')])
            states.append(state_val)

            for i, header in enumerate(headers):
                # Only add values for non-excluded parameters
                if header in values:
                    try:
                        values[header].append(float(parts[i]))
                    except ValueError:
                        continue
        
        # Apply burnin filter
        min_state = min(states)
        burnin_cutoff = np.percentile(states, burnin_fraction * 100)
        print(f"\nDiscarding states from {int(min_state)} up to {int(burnin_cutoff)} as burnin for ESS calculation (burnin_fraction={burnin_fraction})")        
        mask = [s >= burnin_cutoff for s in states]
        for param in values:
            values[param] = [v for v, keep in zip(values[param], mask) if keep]                            

        # Calculate ESS for each parameter
        ess_values = {}
        for param, vals in values.items():
            if len(vals) > 1:
                arr = np.array(vals)
                # Use arviz to calculate ESS
                ess = az.ess(arr)
                ess_values[param] = float(ess)
        
        if not ess_values:
            print(f"Error: No valid ESS values calculated", file=sys.stderr)
            return False, 0, "unknown"
        
        # Find minimum ESS
        min_param = min(ess_values, key=ess_values.get)
        min_val = ess_values[min_param]
        
        # Print summary
        print(f"\nESS Summary:")
        print(f"  Total parameters checked: {len(ess_values)}")
        print(f"  Minimum ESS: {min_val:.2f} ({min_param})")
        
        # Count parameters below threshold
        below_threshold = {k: v for k, v in ess_values.items() if v < min_ess}
        if below_threshold:
            print(f"  Parameters with ESS < {min_ess}: {len(below_threshold)}")
            print(f"\n  Parameters below threshold:")
            for param, ess in sorted(below_threshold.items(), key=lambda x: x[1])[:10]:
                print(f"    {param}: {ess:.2f}")
            if len(below_threshold) > 10:
                print(f"    ... and {len(below_threshold) - 10} more")
        else:
            print(f"  All parameters have ESS >= {min_ess}")
        
        all_above = len(below_threshold) == 0
        return all_above, min_val, min_param
        
    except Exception as e:
        print(f"Error checking ESS: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False, 0, "error"


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python check_beast_ess.py <log_file> [min_ess]")
        print("\nArguments:")
        print("  log_file  : Path to BEAST .log file")
        print("  min_ess   : Minimum ESS threshold (default: 200)")
        sys.exit(1)
    
    min_ess_default = 200
    burnin_fraction = 0.1 
    logFileBaseName = sys.argv[1]
    min_ess = int(sys.argv[2]) if len(sys.argv) > 2 else min_ess_default
    
    merged_logfile = f"{logFileBaseName}.all.log"
    merged_logfile = merge_beast_logfiles(logFileBaseName=logFileBaseName, 
                                          merged_logfile=merged_logfile)

    all_above, min_val, min_param = check_ess_from_log(log_file=merged_logfile, 
                                                       min_ess=min_ess_default,
                                                       burnin_fraction=burnin_fraction)
    
    if min_param == "corrupted_file":
        print(f"\n✗ FATAL ERROR: Log file is corrupted")
        sys.exit(2)
    elif all_above:
        print(f"\n✓ SUCCESS: All ESS values are above {min_ess}")
        sys.exit(0)
    else:
        print(f"\n✗ CONTINUE NEEDED: Some ESS values are below {min_ess}")
        sys.exit(1)


if __name__ == "__main__":
    main()

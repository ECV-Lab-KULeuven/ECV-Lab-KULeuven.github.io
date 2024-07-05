document.addEventListener("DOMContentLoaded", function () {
    console.log("Map renderer script loaded");

    const icons = {
        cafe: '<i class="fas fa-coffee"></i>',
        bar: '<i class="fas fa-beer"></i>',
        restaurant: '<i class="fas fa-utensils"></i>',
        rega: '<i class="fas fa-virus"></i>',
    };

    const pastelColors = {
        cafe: "#FFDFBA",
        bar: "#FFB3BA",
        restaurant: "#BFFFD9",
        rega: "#9faae3",
    };

    async function createMapsFromCodeBlocks() {
        const mapBlocks = document.querySelectorAll("pre code.language-map");
        console.log(`Found ${mapBlocks.length} map blocks`);

        for (const [index, block] of mapBlocks.entries()) {
            console.log(`Processing map block ${block.id}`);
            const mapData = await parseMapData(block.textContent);
            const mapId = `map-${index}`;

            const mapDiv = document.createElement("div");
            mapDiv.id = mapId;
            mapDiv.style.height = "400px";
            mapDiv.style.marginBottom = "1em";

            block.parentNode.parentNode.replaceChild(mapDiv, block.parentNode);

            const map = L.map(mapId).setView(mapData.center, mapData.zoom);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            mapData.markers.forEach((marker) => {
                const iconHtml = icons[marker.type] || "";
                const colorHtml = pastelColors[marker.type] || "";
                L.marker([marker.lat, marker.lng], {
                    icon: L.divIcon({
                        className: "custom-div-icon",
                        html: `<div class='marker-pin' style='background-color:${colorHtml};'></div><div class='marker-text'>${marker.name}</div>${iconHtml}`,
                        iconSize: [30, 42],
                        iconAnchor: [15, 42],
                    }),
                })
                    .addTo(map)
                    .bindPopup(`<strong>${marker.name}</strong><br><a href="${marker.url}">Check on google Maps</a>`);
            });

            console.log(`Map ${index} created`);
        }
    }

    createMapsFromCodeBlocks();
    document.addEventListener("DOMContentSwap", createMapsFromCodeBlocks);
});

async function parseMapData(data) {
    const lines = data.trim().split("\n");
    const markers = [];
    let center = [0, 0];
    let zoom = 14;

    for (const line of lines) {
        if (line.startsWith("center:")) {
            center = line.split(":")[1].split(",").map(Number);
        } else if (line.startsWith("zoom:")) {
            zoom = parseInt(line.split(":")[1]);
        } else {
            const [name, type, lat, lng, url] = line.split(",").map((s) => s.trim()); 
            markers.push({ name, lat, lng, type, url});
        }
    }

    if (markers.length > 0 && center[0] === 0 && center[1] === 0) {
        center = [markers[0].lat, markers[0].lng];
    }

    return { center, zoom, markers };
}

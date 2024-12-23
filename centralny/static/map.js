const osm = "https://www.openstreetmap.org/copyright";
const copy = `© <a href='${osm}'>OpenStreetMap</a>`;
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

/* Create the attribution layer, is this added to the layer group 
   Ah, we use it below in the render_markers() */
const layer = L.tileLayer(url, { attribution: copy });
const map = L.map("map", { layers: [layer] });
// map.fitWorld();
const initial_position = [43, -76.2];
const initial_zoom = 10
map.setView(initial_position, initial_zoom)
var polygon = L.polygon([
    [43.1, -75.9],
    [42.9, -76.1],
    [43.0, -76.0]])
/* Creates the Layer group */
const layerGroup = L.layerGroup().addTo(map);
var drawnItems = new L.featureGroup()
drawnItems.addLayer(polygon)
const layerControl = L.control.layers(drawItems)

// …
async function load_markers() {
  const markers_url = `/centralny/api/markers/?in_bbox=${map
    .getBounds()
    .toBBoxString()}`;
  // console.log("map.js:load_markers, url: " + markers_url)
  const response = await fetch(
    markers_url
  );
  const geojson = await response.json();
  return geojson;
}

async function render_markers() {
  // console.log("map.js:render_markers")
  const markers = await load_markers();
  layerGroup.clearLayers();
  L.geoJSON(markers)
    .bindPopup(
      (layer) =>
        layer.feature.properties.name
    )
    .addTo(layerGroup);
}

map.on("moveend", render_markers)

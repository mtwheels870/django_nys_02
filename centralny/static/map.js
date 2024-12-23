const osm = "https://www.openstreetmap.org/copyright";
const copy = `© <a href='${osm}'>OpenStreetMap</a>`;
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

/* Create the attribution layer, is this added to the layer group 
   Ah, we use it below in the render_markers() */
const layer = L.tileLayer(url, { attribution: copy });
const map = L.map("map", { layers: [layer] });
// map.fitWorld();
const initial_position = [43, -76.2];
const initial_zoom = 8
// map.setView(initial_position, initial_zoom)
map.fitBounds(-75.8, 42.9, -76.2, 43.3);
(initial_position, initial_zoom)
/* Creates the Layer group */
const layerGroup = L.layerGroup().addTo(map);
// var drawnItems = new L.featureGroup()
// drawnItems.addLayer(polygon)
// const layerControl = L.control.layers(drawItems).addTo(map);

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
  // Clears our layer group
  L.geoJSON(markers)
    .bindPopup(
      (layer) =>
        layer.feature.properties.name
    )
    .addTo(layerGroup);
}

async function load_tracts() {
  // const markers_url = `/centralny/api/markers/?in_bbox=${map
  const markers_url = `/centralny/api/tracts/?in_bbox=${map
    .getBounds()
    .toBBoxString()}`;
  // console.log("map.js:load_markers, url: " + markers_url)
  const response = await fetch(
    markers_url
  );
  const geojson = await response.json();
  return geojson;
}

async function render_tracts() {
  // console.log("map.js:render_markers")
  const markers = await load_tracts();
  // Clears our layer group
  L.geoJSON(markers)
    .bindPopup(
      (layer) =>
        layer.feature.properties.short_name
    )
    .addTo(layerGroup);
}

async function render_all() {
  layerGroup.clearLayers();
  render_markers();
  render_tracts();
}

map.on("moveend", render_all)

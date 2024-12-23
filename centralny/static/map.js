const osm = "https://www.openstreetmap.org/copyright";
const copy = `© <a href='${osm}'>OpenStreetMap</a>`;
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

/* Create the attribution layer, is this added to the layer group 
   Ah, we use it below in the render_markers() */
const layer = L.tileLayer(url, { attribution: copy });
const map = L.map("map", { layers: [layer] });
// map.fitWorld();
const initial_position = [43.05, -76.1];
const initial_zoom = 12.5
map.setView(initial_position, initial_zoom)
/* Creates the Layer group */
const layerGroup = L.layerGroup().addTo(map);

async function load_target(url_field) {
  // const markers_url = `/centralny/api/markers/?in_bbox=${map
  const markers_url = `/centralny/api/` + url_field + `/?in_bbox=${map
    .getBounds()
    .toBBoxString()}`;
  // console.log("map.js:load_markers, url: " + markers_url)
  const response = await fetch(
    markers_url
  );
  const geojson = await response.json();
  return geojson;
}

async function render_target(url_component, popup_field, myStyle) {
  console.log("map.js:render_target(), popup_field: " + popup_field)
  const markers = await load_target(url_component);
  // Clears our layer group
  L.geoJSON(markers, { style: myStyle })
    .bindPopup(
      (layer) =>
        layer.feature.properties[popup_field]
    )
    .addTo(layerGroup);
}

async function render_all() {
  zoom = map.getZoom()
  // console.log("render_all(), zoom level: " + zoom)
  layerGroup.clearLayers();
  if (zoom <= 10) {
    render_target('counties', 'county_name', {"color": "#20bb80"})
  } else if (zoom <= 15) {
    render_target('tracts', 'short_name', {"color": "#506030"})
  } else {
    render_target('ip_ranges', 'de_company_name', {"color": "#b030b0"})
  } 
}

map.on("moveend", render_all)


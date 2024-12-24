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

async function render_target(url_component, description, popup_field, myStyle) {
  // console.log("map.js:render_target(), popup_field: " + popup_field)
  const targets = await load_target(url_component);
  // Clears our layer group
  L.geoJSON(targets, { style: myStyle })
    .bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    )
    .addTo(layerGroup);
}

async function render_circle(url_component, description, popup_field, myStyle) {

  // console.log("map.js:render_target(), popup_field: " + popup_field)
  const targets = await load_target(url_component);
  // Clears our layer group
  layer_circle = L.geoJSON(targets, {
      pointToLayer: function(feature, latLong) {
        return new L.CircleMarker(latLong, myStyle);
      }
    }).addTo(layerGroup);
  // We always the circles to be selectable before the polygons
  // layer_circle.bringToFront()
}

async function render_all() {
  zoom = map.getZoom()
  console.log("render_all(), zoom level: " + zoom)
  layerGroup.clearLayers();
  if (zoom <= 10) {
    style = {
      "color": "#20bb80",
      "fillOpacity": 0.25,
      "weight": 3
    }
    render_target('counties', 'County Name', 'county_name', style)
  } else {
      if (zoom >= 14) {
        // Show the actual IP ranges
        var geojsonMarkerOptions = {
            radius: 5,
            fillColor: "#2080b0",
            color: "#000",
            weight: 0.5,
            opacity: 1,
            fillOpacity: 0.5
        };
        render_circle('ip_ranges', 'IP Range: ', 'ip_range_start', geojsonMarkerOptions)
      }
      if (zoom <= 15) {
        circle_style = {
          "color": "#506030",
          "fillOpacity": 0.25,
          "weight": 0.6,
          "radius": 5,
        }
        render_circle('tract_counts', 'IP ranges in Tract: ', 'range_count', circle_style)
        // Tracts + their counts
        style = {
          "color": "#506030",
          "fillOpacity": 0.25,
          "weight": 2,
        }
        render_target('tracts', 'Tract Id: ', 'short_name', style)
        panes = map.getPanes()
        var pane_index = 0
        var num_panes = panes.length
        console.log("draw_tracts(), num_panes = " + num_panes)
      }
  } 
}

map.on("moveend", render_all)


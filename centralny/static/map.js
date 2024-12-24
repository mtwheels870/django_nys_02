const osm = "https://www.openstreetmap.org/copyright";
const copy = `© <a href='${osm}'>OpenStreetMap</a>`;
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

/* Create the attribution layer, is this added to the layer group 
   Ah, we use it below in the render_markers() */
const layer_attribution = L.tileLayer(url, { attribution: copy });
const map = L.map("map", { layers: [layer_attribution] });
// map.fitWorld();
const initial_position = [43.05, -76.1];
const initial_zoom = 12.5
map.setView(initial_position, initial_zoom)
/* Creates the Layer group */
const layerGroup = L.layerGroup().addTo(map);
// const controls = L.control.orderlayers(map)
var baseLayers = { }


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
  return L.geoJSON(targets, { style: myStyle })
    .bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    ).addTo(map);
    // .addTo(layerGroup);
}

async function render_circle(url_component, description, popup_field, myStyle) {

  // console.log("map.js:render_target(), popup_field: " + popup_field)
  const targets = await load_target(url_component);
  // Clears our layer group
  return L.geoJSON(targets, {
      pointToLayer: function(feature, latLong) {
        return new L.CircleMarker(latLong, myStyle);
      }
    }).addTo(map);
  // We always the circles to be selectable before the polygons
  // layer_circle.bringToFront()
}

async function render_all() {
  zoom = map.getZoom()
  console.log("render_all(), zoom level: " + zoom)
  var overlayLayers = {}
  // layerGroup.clearLayers();
  if (zoom <= 10) {
    style = {
      "color": "#20bb80",
      "fillOpacity": 0.25,
      "weight": 3
    }
    layer_counties = render_target('counties', 'County Name', 'county_name', style)
    overlayLayers = {'Counties' : layer_counties }
  } else {
      if (zoom >= 16) {
        // Show the actual IP ranges
        var geojsonMarkerOptions = {
            radius: 5,
            fillColor: "#2080b0",
            color: "#000",
            weight: 0.5,
            opacity: 1,
            fillOpacity: 0.5
        };
        layer_ip_ranges = render_circle('ip_ranges', 'IP Range: ', 'ip_range_start', geojsonMarkerOptions)
        overlayLayers = {'Actual IP Ranges' : layer_ip_ranges }
      } else {
        circle_style = {
          "color": "#506030",
          "fillOpacity": 0.25,
          "weight": 0.6,
          "radius": 5,
          "zIndex": 300,
        }
        layer_centroids = render_circle('tract_counts', 'IP ranges in Tract: ', 'range_count', circle_style)
        // Tracts + their counts
        style = {
          "color": "#506030",
          "fillOpacity": 0.25,
          "weight": 2,
          "zIndex": 400,
        }
        layer_tracts = render_target('tracts', 'Tract Id: ', 'short_name', style)
        overlayLayers = {
            'IP Range Count': layer_centroids,
            'Tracts': layer_controls
        };
        /* panes = map.getPanes()
        var pane_index = 0
        var num_panes = panes.length
        console.log("draw_tracts(), num_panes = " + num_panes) */
      }
      var controls = L.control.orderlayers(baseLayers, overlayLayers, {collapsed: false});
      controls.addTo(map);
  } 
}

map.on("moveend", render_all)


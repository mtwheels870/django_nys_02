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
  return L.geoJSON(targets, { style: myStyle })
    .bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    ).addTo(layerGroup);
}

async function render_circle(url_component, description, popup_field, myStyle) {

  // console.log("map.js:render_target(), popup_field: " + popup_field)
  const targets = await load_target(url_component);
  // Clears our layer group
  return L.geoJSON(targets, {
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
      }
  } 
}

map.on("moveend", render_all)


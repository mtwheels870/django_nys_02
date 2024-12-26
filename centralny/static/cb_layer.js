const styleCounties = {
  color: "#20bb80",
  fillOpacity: 0.25,
  weight: 3
};

const styleIpRanges = {
    radius: 5,
    fillColor: "#2080b0",
    color: "#000",
    weight: 0.5,
    opacity: 1,
    fillOpacity: 0.5
};

const styleTractCounts = {
  color: "#506030",
  fillOpacity: 0.25,
  weight: 0.6,
  radius: 5,
  zIndex: 300,
}

const styleTracts = {
  color: "#506030",
  fillOpacity: 0.25,
  weight: 2,
  zIndex: 400,
}

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

async function render_target(layerGroup, layerControl, url_component, description, popup_field, myStyle) {
  // console.log("map.js:render_target(), popup_field: " + popup_field)
  const targets = await load_target(url_component);
  // Clears our layer group
  var layer = L.geoJSON(targets, { style: myStyle })
    .bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    );
  layer.addTo(layerGroup);
  // layerControl.addOverlay(layer, description);
}

async function render_circle(layerGroup, layerControl, url_component, description, popup_field, myStyle) {

  // console.log("map.js:render_target(), popup_field: " + popup_field)
  const targets = await load_target(url_component);
  // Clears our layer group
  var layer = L.geoJSON(targets, {
      pointToLayer: function(feature, latLong) {
        return new L.CircleMarker(latLong, myStyle);
      }
    }).bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    );
    // console.log("render_circle(), layer: " + layer)
    layer.addTo(layerGroup);
    // layerControl.addOverlay(layer, description);
  // We always the circles to be selectable before the polygons
  // layer_circle.bringToFront()
}

export function cb_render_all(layerGroup, layerControl, zoom) {
  layerGroup.clearLayers();
  console.log("cb_render_all(), zoom level: " + zoom)
  if (zoom <= 10) {
    // Counties
    layerCounties = render_target(layerGroup, layerControl, 'counties', 'County Name', 'county_name', styleCounties)
  } else {
      if (zoom >= 16) {
        // Actual IP ranges
        layer_ip_ranges = render_circle(layerGroup, layerControl, 'ip_ranges', 'Actual IP Range',
            'ip_range_start', styleIpRanges);
      } else {
        // Tracts + their counts
        // render_target(layerGroup, layerControl, 'tracts', 'Tract Id: ', 'short_name', styleTracts)
        // Later in the zList
        layer_centroids = render_circle(layerGroup, layerControl, 'tract_counts', 'Count ranges in Tract ',
            'range_count', styleTractCounts) 
      }
  } 
}

module.export { cb_render_all };

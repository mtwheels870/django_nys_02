class CbLayer {
  constructor(urlComponent, description, popupField, myStyle) {
    this.urlComponent = urlComponent;
    this.description = description;
    this.popupField = popupField;
    this.style = myStyle;
  }
}

const LayerTractCounts extends CbLayer {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }
  renderClass = (layerGroup, layerControl, boundsString) => {
    console.log("LayerTractCounts.renderClass(), this = " + this);
  }
}

const layerTractCounts = new LayerTractCounts("tract_counts", "Aggregated IP Ranges in Tract", "rangeCounts",
  {
    color: "#506030",
    fillOpacity: 0.25,
    weight: 0.6,
    radius: 5,
    zIndex: 300,
  });

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

async function load_target(url_field, boundsString) {
  // const markers_url = `/centralny/api/markers/?in_bbox=${map
  /* const markers_url = `/centralny/api/` + url_field + `/?in_bbox=${map
    .getBounds()
    .toBBoxString()}`; */
  const markers_url = `/centralny/api/` + url_field + `/?in_bbox=` + boundsString;
  // console.log("map.js:load_markers, url: " + markers_url)
  const response = await fetch(
    markers_url
  );
  const geojson = await response.json();
  return geojson;
}

async function render_target(layerGroup, layerControl, url_component, description, popup_field, myStyle, boundsString) {
  // console.log("map.js:render_target(), popup_field: " + popup_field)
  const targets = await load_target(url_component, boundsString);
  // Clears our layer group
  var layer = L.geoJSON(targets, { style: myStyle })
    .bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    );
  layer.addTo(layerGroup);
  // layerControl.addOverlay(layer, description);
}

function onEachCircle(feature, layer) {
  var keys = Object.keys(feature.properties);
  console.log("onEachCircle(), keys.props = " + keys);
/*  if (feature.properties && feature.properies.popupContent) {
    layer.bindPopup(feature.properties.popupContent);
  } */
} 

async function render_circle(layerGroup, layerControl, url_component, description, popup_field, myStyle, boundsString) {

  const targets = await load_target(url_component, boundsString);
  // Clears our layer group
  var layer = L.geoJSON(targets, {
      pointToLayer: function(feature, latLong) {
        return new L.CircleMarker(latLong, myStyle);
      },
      onEachFeature: onEachCircle
    }).bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    );
    // console.log("render_circle(), layer: " + layer)
    layer.addTo(layerGroup);
    // layerControl.addOverlay(layer, description);
  // We always the circles to be selectable before the polygons
  // layer_circle.bringToFront()
}
        layerTractCounts.renderClass(layerGroup, layerControl, boundsString);

export function cb_render_all(layerGroup, layerControl, zoom, boundsString) {
  layerGroup.clearLayers();
  console.log("cb_render_all(), zoom level: " + zoom)
  if (zoom <= 10) {
    // Counties
    var layerCounties = render_target(layerGroup, layerControl, 'counties', 'County Name',
        'county_name', styleCounties, boundsString)
  } else {
      if (zoom >= 16) {
        // Actual IP ranges
        var layer_ip_ranges = render_circle(layerGroup, layerControl, 'ip_ranges', 'Actual IP Range',
            'ip_range_start', styleIpRanges, boundsString);
      } else {
        // Tracts + their counts
        render_target(layerGroup, layerControl, 'tracts', 'Tract Id: ', 'short_name', styleTracts, boundsString)
        // Later in the zList
        layerTractCounts.renderClass(layerGroup, layerControl, boundsString);
        /* var layer_centroids = render_circle(layerGroup, layerControl, 'tract_counts', 'Count ranges in Tract ',
            'range_count', styleTractCounts, boundsString); */
      }
  } 
}

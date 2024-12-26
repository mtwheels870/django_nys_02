// Base Class
class CbLayer {
  constructor(urlComponent, description, popupField, myStyle) {
    console.log("CbLayer.ctor(): type(style): " + typeof(myStyle))
    this.urlComponent = urlComponent;
    this.description = description;
    this.popupField = popupField;
    this.style = myStyle;
  }
}

class LayerCircle extends CbLayer {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }
  // Wrap the render function
  renderClass = (layerGroup, layerControl, boundsString) => {
    console.log("LayerCirc.renderClass(), this = " + this + ", type(): " + typeof(this));
    // Call render circle
    render_circle(this, layerGroup, layerControl, boundsString);
  }
}

// Sub Class
class LayerTractCounts extends LayerCircle {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }

  // Inside a class, format if methodName: function
  onEachCircle = (feature, layer) => {
    var keys = Object.keys(feature.properties);
    var rangeCount = feature.properties["range_count"]
    var radiusGraduated;
    if (rangeCount <= 60) {
      radiusGraduated = 2;
    } else if (rangeCount <= 120) {
      radiusGraduated = 4;
    } else if (rangeCount <= 180) {
      radiusGraduated = 6;
    } else {
      radiusGraduated = 8;
    }
    console.log("LTC.onEachCircle(), feature.props = " + keys + ", range_count = " + rangeCount);
    var copiedStyle = {...this.style};
    console.log("      style: ");
    for (const key in copiedStyle) {
      console.log("  " + key + ": " + copiedStyle[key]);
    } 
    layer.setStyle(copiedStyle)

  /*  if (feature.properties && feature.properies.popupContent) {
      layer.bindPopup(feature.properties.popupContent);
    } */
  } 
}

// Instantiate
const layerTractCounts = new LayerTractCounts("tract_counts", "Aggregated IP Ranges in Tract", "rangeCounts",
  {
    color: "#506030",
    fillOpacity: 0.25,
    weight: 0.6,
    radius: 5,
    zIndex: 300,
  }
);

class LayerIpRanges extends LayerCircle {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }

  // Inside a class, format if methodName: function
  onEachCircle = (feature, layer) => {
    var keys = Object.keys(feature.properties);
    console.log("LIP.onEachCircle(), feature.props = " + keys);
    layer.setStyle(this.style);
  } 
};

// Instantiate
const layerIpRanges = new LayerIpRanges ("ip_ranges", "Actual IP Range", "ip_range_start",
  {
    radius: 5,
    fillColor: "#2080b0",
    color: "#000",
    weight: 0.5,
    opacity: 1,
    fillOpacity: 0.5
  }
);

const styleCounties = {
  color: "#20bb80",
  fillOpacity: 0.25,
  weight: 3
};

const styleTracts = {
  color: "#506030",
  fillOpacity: 0.25,
  weight: 2,
  zIndex: 400,
}

async function load_target(url_field, boundsString) {
  const markers_url = `/centralny/api/` + url_field + `/?in_bbox=` + boundsString;
  const response = await fetch(
    markers_url
  );
  const geojson = await response.json();
  return geojson;
}

async function render_target(layerGroup, layerControl, url_component, description, popup_field, myStyle, boundsString) {
  const targets = await load_target(url_component, boundsString);
  // Clears our layer group
  var layer = L.geoJSON(targets, { style: myStyle })
    .bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    );
  layer.addTo(layerGroup);
  // layerControl.addOverlay(layer, description);
}

async function render_circle(classObject, layerGroup, layerControl, boundsString) {
  console.log("render_circle(), myStyle = " + classObject + ", type = " + typeof(classObject))
  const targets = await load_target(classObject.urlComponent, boundsString);
  // Clears our layer group
    console.log("render_circle(), type(style) = " + typeof(classObject.myStyle))
    var layer = L.geoJSON(targets, {
      pointToLayer: function(feature, latLong) {
        return new L.CircleMarker(latLong, classObject.myStyle);
      },
      onEachFeature: classObject.onEachCircle,
    }).addTo(layerGroup);
    // layer.bringToFront();
}

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
        layerIpRanges.renderClass(layerGroup, layerControl, boundsString)
      } else {
        // Tracts + their counts
        // render_target(layerGroup, layerControl, 'tracts', 'Tract Id: ', 'short_name', styleTracts, boundsString)
        // Later in the zList
        layerTractCounts.renderClass(layerGroup, layerControl, boundsString);
      }
  } 
}

/* .bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    ); */
    // console.log("render_circle(), layer: " + layer)
    // layer.addTo(layerGroup);
    // layerControl.addOverlay(layer, description);
  // We always the circles to be selectable before the polygons
  // layer_circle.bringToFront()
        /* var layer_centroids = render_circle(layerGroup, layerControl, 'tract_counts', 'Count ranges in Tract ',
            'range_count', styleTractCounts, boundsString); */
  // console.log("map.js:render_target(), popup_field: " + popup_field)
  // const markers_url = `/centralny/api/markers/?in_bbox=${map
  /* const markers_url = `/centralny/api/` + url_field + `/?in_bbox=${map
    .getBounds()
    .toBBoxString()}`; */
  // ddconsole.log("map.js:load_markers, url: " + markers_url)
  // Wrap the render function
  /* renderClass = (layerGroup, layerControl, boundsString) => {
    console.log("LIP.renderClass(), this = " + this + ", type: " + typeof(this));
    // Call render circle
    // var foreachFunction = this.onEachCircle;
    render_circle(this, layerGroup, layerControl,
      boundsString);
  } */
  /*  if (feature.properties && feature.properies.popupContent) {
      layer.bindPopup(feature.properties.popupContent);
    } */
  // Wrap the render function
  /* renderClass = (layerGroup, layerControl, boundsString) => {
    console.log("LTC.renderClass(), this = " + this + ", type(): " + typeof(this));
    // Call render circle
    // var foreachFunction = this.onEachCircle;
    render_circle(this, layerGroup, layerControl,
      boundsString); 
  } */
/*    for (const key in myStyle) {
      console.log("  style, " + key + ": " + myStyle[key]);
    } */
    // console.log("CbLayer.ctor(), myStyle = " + myStyle);

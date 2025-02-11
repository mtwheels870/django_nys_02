/*
 * Base Class
 */ 
class CbLayer {
  constructor(urlComponent, description, popupField, myStyle) {
    this.urlComponent = urlComponent;
    this.description = description;
    this.popupField = popupField;
    this.style = myStyle;
  }
}

/*
 * Circle (intermediate)
 */ 
class LayerCircle extends CbLayer {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }
  // Wrap the render function
  renderClass = (layerGroup, layerControl, boundsString) => {
    // Call render circle
    render_circle(this, layerGroup, layerControl, boundsString);
  }
}

function tract_count_clicked(censusTract) {
    console.log('tract_count_clicked(), censusTract = ' + censusTract);
};

/*
 * TractCounts -> Circle -> Base
 */ 
class LayerTractCounts extends LayerCircle {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }

  // Inside a class, format if methodName: function
  onEachCircle = (feature, layer) => {
    // Do the graduated circle
    var rangeCount = feature.properties["range_count"]
    // range 1... 100 ... 200 ... 400
    var radiusGraduated = Math.ceil(rangeCount / 120) * 3.5;
    var copiedStyle = {...this.style};
    copiedStyle["radius"] = radiusGraduated;
    layer.setStyle(copiedStyle)
    var censusTract = feature.properties["census_tract"]
    layer.bindPopup("<b>(Circle) Census Tract: " + censusTract + "<br>IP Range Count: " + rangeCount + "</b>")
    // Doesn't work: layer.on('click', function(e) {
    /* this.on('click', function(e) {
        alert('censusTractCircle(), censusTract = ' + censusTract)
    } ) */
    // layer.on('click', tract_count_clicked, censusTract)
  } 
}

// Instantiate
//   radius: 5, weight: 0.6,
const layerTractCounts = new LayerTractCounts("tract_counts", "Aggregated IP Ranges in Tract", "range_count",
  { color: "#2F118F", fillOpacity: 0.80, weight: 0, zIndex: 300, }
);


/*
 * CountyCounts -> Circle -> Base
 */ 
class LayerCountyCounts extends LayerCircle {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }

  // Inside a class, format if methodName: function
  onEachCircle = (feature, layer) => {
    // Do the graduated circle
    var rangeCount = feature.properties["range_count"]
    var radiusGraduated;
    if (rangeCount <= 500) {
      radiusGraduated = 5;
    } else if (rangeCount <= 2000) {
      radiusGraduated = 10;
    } else {
      radiusGraduated = 15;
    }
    var copiedStyle = {...this.style};
    copiedStyle["radius"] = radiusGraduated;
    layer.setStyle(copiedStyle)
    var countyCode = feature.properties["county_code"]
    layer.bindPopup("<b>County: " + countyCode + "<br>IP Range Count: " + rangeCount + "</b>")
  } 
}

// Instantiate
const layerCountyCounts = new LayerCountyCounts("county_counts", "Aggregated IP Ranges in County", "range_counts",
  { color: "#20bb80", fillOpacity: 0.80, weight: 0, zIndex: 300, }
);

/*
 * IP Ranges -> Circle -> Base
 */ 
class LayerIpRanges extends LayerCircle {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }

  // Inside a class, format if methodName: function
  onEachCircle = (feature, layer) => {
    var keys = Object.keys(feature.properties);
    console.log("LIP.onEachCircle(), feature.props = " + keys);
    layer.setStyle(this.style);
    var ipRangeStart = feature.properties["ip_range_start"]
    var companyName = feature.properties["de_company_name"]
    layer.bindPopup("<b>First IP Range (@ this location):<br>IP Range Start:" + ipRangeStart + 
        "<br>Company Name: " + companyName + "</b>")
  } 
};

// Instantiate
const layerIpRanges = new LayerIpRanges ("ip_ranges", "Actual IP Range", "ip_range_start",
  { radius: 7, fillColor: "#9A0669", color: "#000", weight: 0, fillOpacity: 0.8 }
);


/*
 * Polygon 
 */ 
class LayerPolygon extends CbLayer {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }
  // Wrap the render function
  renderClass = (layerGroup, layerControl, boundsString) => {
    // Call render circle
    render_target(this, layerGroup, layerControl, boundsString);
  }
}

// Instantiate Tractgs
const layerTracts = new LayerPolygon('tracts', 'Tract Id: ', 'short_name', 
{ color: "#2F118F", fillOpacity: 0.25, weight: 0.5, zIndex: 400 })

// Instantiate Counties
const layerCounties = new LayerPolygon('counties', 'County Name', 'county_name',
{ color: "#20bb80", fillOpacity: 0.25, weight: 1, zIndex: 400 })

async function load_target(url_field, boundsString) {
  const markers_url = `/centralny/api/` + url_field + `/?in_bbox=` + boundsString;
  const response = await fetch(
    markers_url
  );
  const geojson = await response.json();
  return geojson;
}

async function unused_render_target(layerGroup, layerControl, url_component, description, popup_field, myStyle, boundsString) {
  const targets = await load_target(url_component, boundsString);
  // Clears our layer group
  var layer = L.geoJSON(targets, { style: myStyle })
    .bindPopup(
      (layer) => description + ": <b>" + layer.feature.properties[popup_field] + "</b>"
    );
  layer.addTo(layerGroup);
  // layerControl.addOverlay(layer, description);
}

async function render_target(classObject, layerGroup, layerControl,boundsString) {
  const targets = await load_target(classObject.urlComponent, boundsString);
  // Clears our layer group
  // console.log("render_target(). style = " + classObject.style);
  L.geoJSON(targets, { style: classObject.style })
    .bindPopup(
      (layer) => classObject.description + ": <b>" + layer.feature.properties[classObject.popupField] + "</b>")
    .addTo(layerGroup);
}

async function render_circle(classObject, layerGroup, layerControl, boundsString) {
  const targets = await load_target(classObject.urlComponent, boundsString);
    var layer = L.geoJSON(targets, {
      pointToLayer: function(feature, latLong) {
        return new L.CircleMarker(latLong, classObject.myStyle);
      },
      onEachFeature: classObject.onEachCircle,
    }).addTo(layerGroup);
}

export function cb_render_all(layerGroupAll, layerControl, zoom, boundsString) {
  layerGroupAll.clearLayers();
  // var layerGroupPolys = L.layerGroup().addTo(layerGroupAll);
  // var layerGroupCircles = L.layerGroup().addTo(layerGroupAll);
    
  // console.log("cb_render_all(), zoom level: " + zoom)
  if (zoom <= 10) {
    // Counties
    layerCountyCounts.renderClass(layerGroupAll, layerControl, boundsString);
    layerCounties.renderClass(layerGroupAll, layerControl, boundsString);
  } else if (zoom >= 15) {
    // Actual IP ranges
    layerIpRanges.renderClass(layerGroupAll, layerControl, boundsString);
  } else {
    // Tracts + their counts
    layerTracts.renderClass(layerGroupAll, layerControl, boundsString);
    layerTractCounts.renderClass(layerGroupAll, layerControl, boundsString);
  } 
  // layerGroupPolys.setZIndex(400);
  // layerGroupCircles.setZIndex(200);
  debug_layers(layerGroupAll);
}

function debug_layers(lg) {
  layers = lg.getLayers();
  for (i = 0; i < layers.length; i++) {
    layer = layers[i];
    style = layer.style;
    console.log('d_l(), layer[' + i + '], style = ' + style);
  }
}


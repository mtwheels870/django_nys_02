/*
 * Base Class
 */ 
// Don't do this! import { map_wrapper } from "./map.js";

let _myMapWrapper;

function debug_layers(lg) {
  var layers = lg.getLayers();
  var num_layers = layers.length;
  console.log('d_l(), num_layers = ' + num_layers);
  for (var i = 0; i < num_layers; i++) {
    layer = layers[i];
    style = layer.style;
    console.log('d_l(), layer[' + i + '], style = ' + style);
  }
}

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
  renderClass = (boundsString) => {
    // Call render circle
    render_circle(this, boundsString);
  }
}

function handleCircleClick(context, e) {
  console.log("Clicked marker with context:", context);
  console.log("Event: ", e);
  map = _myMapWrapper.map;
  console.log("map : ", map);
  const form1 = document.forms['selected_tract_form'];
  /* console.log('circle_clicked(), form1 = ' + form1);
  for (const [key, value] of Object.entries(form1)) {
    console.log(`${key}: ${value}`)
  } */
  form1["id"].value = context["id"]
  form1["agg_type"].value = context["agg_type"]
  var boundsString = _myMapReference.getBounds().toBBoxString()
  form1["map_bbox"].value = boundsString;
  form1.submit()
}

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
    // console.log('ltc.oEC(), copiedStyle = ' + JSON.stringify(copiedStyle));
    copiedStyle["radius"] = radiusGraduated;
    layer.setStyle(copiedStyle)
    var id = feature["id"]
    var censusTract = feature.properties["census_tract"]
    layer.bindPopup("<b>(Circle) Census Tract: " + censusTract + "<br>IP Range Count: " + 
            rangeCount + "<br>Database ID: " + id + "</b>")
    let context = { agg_type: "CountRangeTract", id: id };
    layer.on('click', handleCircleClick.bind(null, context));
  }
}

// Instantiate
//   radius: 5, weight: 0.6,
const layerTractCounts = new LayerTractCounts("tract_counts", "Aggregated IP Ranges in Tract", "range_count",
  { color: "#2F118F", fillOpacity: 0.80, weight: 0, pane: 'circles'}
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
    var id = feature["id"]
    layer.bindPopup("<b>County: " + countyCode + "<br>IP Range Count: " + rangeCount + "<br>ID: " + id + "</b>")
    let context = { agg_type: "CountRangeCounty", id: id };
    layer.on('click', handleCircleClick.bind(null, context));
  } 
}

// Instantiate
const layerCountyCounts = new LayerCountyCounts("county_counts", "Aggregated IP Ranges in County", 
    "range_counts", { color: "#20bb80", fillOpacity: 0.80, weight: 0, zIndex: 300, }
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
    // console.log("LIP.onEachCircle(), feature.props = " + keys);
    layer.setStyle(this.style);
    // console.log("LIP.onEachCircle(), feature.props = " + keys);
    var id = feature["id"]
    var ipRangeStart = feature.properties["ip_range_start"]
    var companyName = feature.properties["company_name"]
    layer.bindPopup("<b>First IP Range (@ this location):<br>IP Range Start:" + ipRangeStart + 
        "<br>Company Name: " + companyName + "<br>ID: " + id + "</b>")
    let context = { agg_type: "DeIpRange", id: id };
    layer.on('click', handleCircleClick.bind(null, context));
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
  renderClass = (map, layerGroup, layerControl, boundsString) => {
    // Call render circle
    render_target(this, boundsString);
  }
}

// Instantiate Tractgs
const layerTracts = new LayerPolygon('tracts', 'Tract Id: ', 'short_name', 
{ color: "#2F118F", fillOpacity: 0.25, weight: 0.5, zIndex: 200 })

// Instantiate Counties
const layerCounties = new LayerPolygon('counties', 'County Name', 'county_name',
{ color: "#20bb80", fillOpacity: 0.25, weight: 1, zIndex: 200 })

async function load_target(url_field, boundsString) {
  const markers_url = `/centralny/api/` + url_field + `/?in_bbox=` + boundsString;
  const response = await fetch(
    markers_url
  );
  const geojson = await response.json();
  return geojson;
}

async function render_target(classObject, boundsString) {
  var layerGroup = _myMapWrapper.layerGroupAll;
  console.log('render_target(), layerGroup = ' + layerGroup);
  const targets = await load_target(classObject.urlComponent, boundsString);
  // var debug = JSON.stringify(layer.feature.properties);
  // console.log('render_target(), debug = ' + debug);
    // console.log('ltc.oEC(), copiedStyle = ' + JSON.stringify(copiedStyle));
  // Clears our layer group
  // console.log("render_target(). style = " + classObject.style);
  L.geoJSON(targets, { style: classObject.style })
    .bindPopup(
      (layer) => classObject.description + ": <b>" + 
        layer.feature.properties[classObject.popupField] + "</b>")
    .addTo(layerGroup);
}

async function render_circle(classObject, boundsString) {
  var map = _myMapWrapper.map;
  const targets = await load_target(classObject.urlComponent, boundsString);
    var layer = L.geoJSON(targets, {
      pointToLayer: function(feature, latLong) {
        return new L.CircleMarker(latLong, classObject.myStyle);
      },
      onEachFeature: classObject.onEachCircle,
      pane: 'circles',
    }).addTo(map);
}

export function cb_render_all(map_wrapper, zoom, boundsString) {
  _myMapWrapper = map_wrapper;
  console.log("cb_render_all(), _myMapWrapper = " + _myMapWrapper );
  var layerGroupAll = map_wrapper.layerGroupAll 
  // var layerControl = map_wrapper.layerControl
  layerGroupAll.clearLayers();
  if (zoom <= 10) {
    // Counties
    layerCountyCounts.renderClass(boundsString);
    layerCounties.renderClass(boundsString);
  } else if (zoom >= 15) {
    // Actual IP ranges
    layerIpRanges.renderClass(boundsString);
  } else {
    // Tracts + their counts
    layerTracts.renderClass(boundsString);
    layerTractCounts.renderClass(boundsString);
  } 
}

    // Doesn't work: layer.on('click', function(e) {
    /* this.on('click', function(e) {
        alert('censusTractCircle(), censusTract = ' + censusTract)
    } ) */
    // layer.on('click', tract_count_clicked, censusTract)
    /* var debug = JSON.stringify(layer.feature);
    console.log('LTC.oEC(), debug = ' + debug); */

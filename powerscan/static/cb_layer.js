/*
 * Base Class
 */ 
// Don't do this! import { map_wrapper } from "./map.js";

// We use this global to save state (hack)
let _myMapWrapper;

let _layersToDelete = []

export const CIRCLE_PANE = 'circles';

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
  var map = _myMapWrapper.map;
  console.log("map : ", map);
  const form1 = document.forms['selected_tract_form'];
  form1["id"].value = context["id"];
  form1["agg_type"].value = context["agg_type"];
  var boundsString = map.getBounds().toBBoxString();
  form1["map_bbox"].value = "in_bbox=" + boundsString;
  form1["range_count"].value = context["range_count"];
  form1.submit();
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
    var range_count = feature.properties["range_count"]
    // range 1... 100 ... 200 ... 400
    // Central_NY: var radiusGraduated = Math.ceil(range_count / 120) * 3.5;
    // LA, DigEl: var radiusGraduated = Math.ceil(range_count / 4000) * 3.5;
    // THis version LA, MaxM
    var radiusGraduated = Math.ceil(range_count / 400) * 3.5;
    var copiedStyle = {...this.style};
    // console.log('ltc.oEC(), copiedStyle = ' + JSON.stringify(copiedStyle));
    copiedStyle["radius"] = radiusGraduated;
    layer.setStyle(copiedStyle)
    var id = feature["id"]
    var censusTract = feature.properties["census_tract"]
    layer.bindPopup("<b>(Circle) Census Tract: " + censusTract + "<br>IP Range Count: " + 
            range_count + "<br>Database ID: " + id + "</b>")
    /* layer.bindPopup("<b>(Circle) Census Tract: " + censusTract + "<br>IP Range Count: " + 
            range_count + "<br>Database ID: " + id + "</b>") */
    let context = { agg_type: "CountRangeTract", id: id, range_count : range_count };
    layer.on('click', handleCircleClick.bind(null, context));
  }
}

// Instantiate
//   radius: 5, weight: 0.6,
const layerTractCounts = new LayerTractCounts("tract_counts", "Aggregated IP Ranges in Tract", "range_count",
  { color: "#246bb3", fillOpacity: 0.80, weight: 0, pane: CIRCLE_PANE}
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
    var range_count = feature.properties["range_count"]
    var radiusGraduated;
    // This version - MaxMind, SE US
    if (range_count <= 1000) {
      radiusGraduated = 3;
    } else if (range_count <= 2000) {
      radiusGraduated = 5;
    } else if (range_count <= 10000) {
      radiusGraduated = 10;
    } else {
      radiusGraduated = 15;
    }
    var copiedStyle = {...this.style};
    copiedStyle["radius"] = radiusGraduated;
    layer.setStyle(copiedStyle)
    var countyCode = feature.properties["county_code"]
    var id = feature["id"]
    // layer.bindPopup("<b>County: " + countyCode + "<br>IP Range Count: " + range_count + "<br>ID: " + id + "</b>")
    layer.bindPopup("<b>County: " + countyCode + "<br>IP Range Count: " + range_count + 
        "<br>ID: " + id + "</b>")
    let context = { agg_type: "CountRangeCounty", id: id, range_count: range_count };
    layer.on('click', handleCircleClick.bind(null, context));
  } 
}

// Instantiate
const layerCountyCounts = new LayerCountyCounts("county_counts", "Aggregated IP Ranges by County", 
    "range_counts", { color: "#24b3b3", fillOpacity: 0.80, weight: 0, zIndex: 300, }
);

/*
 * CountyCounts -> Circle -> Base
 */ 
class LayerStateCounts extends LayerCircle {
  constructor(urlComponent, description, popupField, myStyle) {
    super(urlComponent, description, popupField, myStyle);
  }

  // Inside a class, format if methodName: function
  onEachCircle = (feature, layer) => {
    // Do the graduated circle
    var range_count = feature.properties["range_count"]
    var radiusGraduated;
    // This version - MaxMind, SE US
    if (range_count <= 5000) {
      radiusGraduated = 3;
    } else if (range_count <= 100000) {
      radiusGraduated = 5;
    } else if (range_count <= 200000) {
      radiusGraduated = 10;
    } else {
      radiusGraduated = 15;
    }
    var copiedStyle = {...this.style};
    copiedStyle["radius"] = radiusGraduated;
    layer.setStyle(copiedStyle)
    var countyCode = feature.properties["county_code"]
    var model_b_field = feature.properties["model_b_field"]
    var id = feature["id"]
    // layer.bindPopup("<b>State: " + model_b_field + "<br>IP Range Count: " + range_count + "<br>ID: " + id + "</b>")
    layer.bindPopup("<b>State: ${model_b_field}<br>IP Range Count: ${range_count.toLocaleString()}<br>" +
        "ID: ${id}</b>")
    let context = { agg_type: "CountRangeState", id: id, range_count: range_count };
    layer.on('click', handleCircleClick.bind(null, context));
  } 
}

const layerStateCounts = new LayerStateCounts("state_counts", "Aggregated IP Ranges by State", 
    "range_counts", { color: "#24b324", fillOpacity: 0.80, weight: 0, zIndex: 300, }
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
    layer.setStyle(this.style);
    var id = feature["id"]
    var ipRangeStart = feature.properties["ip_range_start"]
    var companyName = feature.properties["company_name"]
    layer.bindPopup("<b>First IP Range (@ this location):<br>IP Range Start:" + ipRangeStart + 
        "<br>Company Name: " + companyName + "<br>ID: " + id + "</b>")
    let range_count = 1;
    let context = { agg_type: "DeIpRange", id: id, range_count : range_count };
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
  renderClass = (boundsString) => {
    // Call render circle
    render_target(this, boundsString);
  }
}

// Instantiate Tractgs
// urlComponent (see powerscan/apis.py), description, popupField
const layerTracts = new LayerPolygon('tracts', 'Tract Id: ', 'name', 
{ color: "#246bb3", fillOpacity: 0.25, weight: 0.5, zIndex: 200 })

// Instantiate Counties
const layerCounties = new LayerPolygon('counties', 'County Name', 'county_name',
{ color: "#24b3b3", fillOpacity: 0.25, weight: 1, zIndex: 200 })

const layerStates = new LayerPolygon('states', 'State Name', 'state_name',
{ color: "#24b324", fillOpacity: 0.25, weight: 1, zIndex: 200 })

async function load_target(url_field, boundsString) {
  try {
    const markers_url = `/powerscan/api/` + url_field + `/?in_bbox=` + boundsString;
    console.log("load_target(), url = " + markers_url);
    const response = await fetch(
      markers_url
    );
    // If disconnected, the above actually throws a TypeError (doesn't get here)
    if (!response.ok) {
      throw new Error("HTTP error! url: " + markers_url + ", status: " + response.status);
    }
    const geojson = await response.json();
    return geojson;
  } catch (error) {
    console.error("Fetch error: ", error);
    throw error;
  }
}

async function render_target(classObject, boundsString) {
  var layerGroup = _myMapWrapper.layerGroupAll;
  const targets = await load_target(classObject.urlComponent, boundsString);
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
      pane: CIRCLE_PANE,
    }).addTo(map);
}

function clear_existing_layers(map_wrapper) {
  // Clear the layerGroupAll, which are just polygons
  var layerGroupAll = map_wrapper.layerGroupAll 
  layerGroupAll.clearLayers();

  // Circles are in their own pane
  var map = map_wrapper.map;
  if (_layersToDelete.length > 0) {
    console.log('clear_existing(), we have layers in our array! (shouldn.t)');
  }
  var circle_pane = map_wrapper.map.getPane(CIRCLE_PANE);

  // Iterate through all layers in the map.  Any on the circle pane get put onto our delete list
  map.eachLayer(function(layer) {
    var layer_pane = layer.getPane();
    if (layer_pane === circle_pane) {
        _layersToDelete.push(layer);
    } 
  });

  // Delete each of the layers on 
  while (_layersToDelete.length > 0) {
    let layer = _layersToDelete.pop();
    map.removeLayer(layer);
  }
}

export function cb_render_all(map_wrapper, zoom, boundsString) {
  _myMapWrapper = map_wrapper;
  var partialBoundsString = boundsString.substring(0, 12);
 
  clear_existing_layers(map_wrapper);
  console.log("cb_render_all(), zoom = " + zoom + ", boundsString = " + 
        partialBoundsString);
  // var layerControl = map_wrapper.layerControl
  if (zoom <= 7) {
    layerStateCounts.renderClass(boundsString);
    layerStates.renderClass(boundsString); 
  } else if (zoom <= 10) {
    // Counties
    layerCountyCounts.renderClass(boundsString);
    layerCounties.renderClass(boundsString);
  } else if (zoom >= 15) {
    // Actual IP ranges
    layerIpRanges.renderClass(boundsString);
  } else {
    // Tracts + their counts
    layerTracts.renderClass(boundsString);
    // layerTractCounts.renderClass(boundsString);
  } 
}

  /* let layers = layerGroupAll.getLayers();
  for (let i = 0; i < layers.length; i++) {
    let layer = layers[i];
    console.log('cb_render_all(), layer[' + i + '] (pane): ' + layer.pane);

  } */
    /* Central NY, DigEl: if (range_count <= 500) {
      radiusGraduated = 5;
    } else if (range_count <= 2000) {
      radiusGraduated = 10;
    } else {
      radiusGraduated = 15;
    } */
   /*  LA, DigEl: if (range_count <= 20000) {
      radiusGraduated = 5;
    } else if (range_count <= 60000) {
      radiusGraduated = 10;
    } else {
      radiusGraduated = 15;
    } */

/*
 * Base Class
 */ 
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
  renderClass = (map, layerGroup, layerControl, boundsString) => {
    // Call render circle
    render_circle(this, map, layerGroup, layerControl, boundsString);
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
    // console.log('ltc.oEC(), copiedStyle = ' + JSON.stringify(copiedStyle));
    copiedStyle["radius"] = radiusGraduated;
    layer.setStyle(copiedStyle)
    var debug = JSON.stringify(layer.feature);
    console.log('LTC.oEC(), debug = ' + debug);
    var id = feature["id"]
    var censusTract = feature.properties["census_tract"]
    layer.bindPopup("<b>(Circle) Census Tract: " + censusTract + "<br>IP Range Count: " + 
            rangeCount + "<br>Database ID: " + id + "</b>")
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
    console.log("LIP.onEachCircle(), feature.props = " + keys);
    layer.setStyle(this.style);
    // console.log("LIP.onEachCircle(), feature.props = " + keys);
    var ip = feature["id"]
    var ipRangeStart = feature.properties["ip_range_start"]
    var companyName = feature.properties["company_name"]
    layer.bindPopup("<b>First IP Range (@ this location):<br>IP Range Start:" + ipRangeStart + 
        "<br>Company Name: " + companyName + "<br>ID: " + id + "</b>")
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
    render_target(this, map, layerGroup, layerControl, boundsString);
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

async function render_target(classObject, map, layerGroup, layerControl,boundsString) {
  const targets = await load_target(classObject.urlComponent, boundsString);
  // var debug = JSON.stringify(layer.feature.properties);
  // console.log('render_target(), debug = ' + debug);
    // console.log('ltc.oEC(), copiedStyle = ' + JSON.stringify(copiedStyle));
  // Clears our layer group
  // console.log("render_target(). style = " + classObject.style);
  L.geoJSON(targets, { style: classObject.style })
    .bindPopup(
      (layer) => classObject.description + ": <b>id = ??" + 
        layer.feature.properties[classObject.popupField] + "</b>")
    .addTo(layerGroup);
}

async function render_circle(classObject, map, layerGroup, layerControl, boundsString) {
  const targets = await load_target(classObject.urlComponent, boundsString);
    var layer = L.geoJSON(targets, {
      pointToLayer: function(feature, latLong) {
        var layer = new L.CircleMarker(latLong, classObject.myStyle);
        layer.on('click', function(e) {
          console.log('circle clicked');
        });
        return layer;
      },
      onEachFeature: classObject.onEachCircle,
      pane: 'circles',
    }).addTo(map);
}

export function cb_render_all(map, layerGroupAll, layerControl, zoom, boundsString) {
  layerGroupAll.clearLayers();
  if (zoom <= 10) {
    // Counties
    layerCountyCounts.renderClass(map, layerGroupAll, layerControl, boundsString);
    layerCounties.renderClass(map, layerGroupAll, layerControl, boundsString);
  } else if (zoom >= 15) {
    // Actual IP ranges
    layerIpRanges.renderClass(map, layerGroupAll, layerControl, boundsString);
  } else {
    // Tracts + their counts
    layerTracts.renderClass(map, layerGroupAll, layerControl, boundsString);
    layerTractCounts.renderClass(map, layerGroupAll, layerControl, boundsString);
  } 
}

    // Doesn't work: layer.on('click', function(e) {
    /* this.on('click', function(e) {
        alert('censusTractCircle(), censusTract = ' + censusTract)
    } ) */
    // layer.on('click', tract_count_clicked, censusTract)

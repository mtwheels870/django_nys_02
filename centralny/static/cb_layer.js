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
    layer.bindPopup("<b>Census Tract: " + censusTract + "<br>IP Range Count: " + rangeCount + "</b>")
    layer.on('click', function(e) {
        console.log('censusTractCircle(), censusTract = ' + censusTract)
    } )
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

async function render_target3(layerGroup, layerControl, url_component, description, popup_field, myStyle, boundsString) {
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

export function cb_render_all(layerGroup, layerControl, zoom, boundsString) {
  layerGroup.clearLayers();
  // console.log("cb_render_all(), zoom level: " + zoom)
  if (zoom <= 10) {
    // Counties
    layerCountyCounts.renderClass(layerGroup, layerControl, boundsString);
    layerCounties.renderClass(layerGroup, layerControl, boundsString);
  } else if (zoom >= 15) {
    // Actual IP ranges
    layerIpRanges.renderClass(layerGroup, layerControl, boundsString);
  } else {
    // Tracts + their counts
    layerTracts.renderClass(layerGroup, layerControl, boundsString);
    layerTractCounts.renderClass(layerGroup, layerControl, boundsString);
  } 
  // debug_layers(layerGroup, layerControl);
}

function debug_layers(layerGroup, layerControl) {
  console.log("Layer Group:");
  var i = 0;
  for (const layer in layerGroup) {
    // name = layerGroup[i].name
    // console.log("layer[" + i + "]: " + name);
    /* for (const key in layerGroup[i]) {
    } */
    i = i + 1;
  }
  // var keys = Object.keys(feature.properties);
  /* console.log("      style: ");
  for (const key in copiedStyle) {
    console.log("  " + key + ": " + copiedStyle[key]);
  }  */

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
    /* if (rangeCount <= 60) {
      radiusGraduated = 2;
    } else if (rangeCount <= 120) {
      radiusGraduated = 4;
    } else if (rangeCount <= 180) {
      radiusGraduated = 6;
    } else {
      radiusGraduated = 8;
    } */
    // var keys = Object.keys(feature.properties);
    /* console.log("      style: ");
    for (const key in copiedStyle) {
      console.log("  " + key + ": " + copiedStyle[key]);
    }  */
    /* console.log("LTC.onEachCircle(), feature.props = " + keys + ", range_count = " + rangeCount); */
  // console.log("render_circle(), myStyle = " + classObject + ", type = " + typeof(classObject))
  // Clears our layer group
    // console.log("render_circle(), type(style) = " + typeof(classObject.myStyle))
  /*  if (feature.properties && feature.properies.popupContent) {
      layer.bindPopup(feature.properties.popupContent);
    } */
    // console.log("LayerCirc.renderClass(), this = " + this + ", type(): " + typeof(this));
    //  layer.addTo(layerGroup);
  // layerControl.addOverlay(layer, description);
/* const styleTracts = {
  color: "#506030",
  fillOpacity: 0.25,
  weight: 2,
  zIndex: 400,
} */
/* const styleCounties = {
  color: "#20bb80",
  fillOpacity: 0.25,
  weight: 3
}; */
    // render_target(layerGroup, layerControl, 'tracts', 'Tract Id: ', 'short_name', styleTracts, boundsString)
    // render_target(layerGroup, layerControl, 'tracts', 'Tract Id: ', 'short_name', styleTracts, boundsString)
    // Later in the zList
    /* var layerCounties = render_target(layerGroup, layerControl, 'counties', 'County Name',
        'county_name', styleCounties, boundsString);  */

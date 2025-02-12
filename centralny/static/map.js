import { cb_render_all } from './cb_layer.js';

// Create the map
// export const map = L.map("map", { layers: [layerOsm] });

export let map;
if (typeof map == "undefined") {
    const osm = "https://www.openstreetmap.org/copyright";
    const copy = `© <a href='${osm}'>OpenStreetMap</a>`;
    const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

    /* Create the attribution layer, is this added to the layer group 
       Ah, we use it below in the render_markers() */
    const layerOsm = L.tileLayer(url, { attribution: copy });
    console.log("map is already defined");
    const initial_position = [43.05, -76.1];
    const initial_zoom = 12.5
    map = L.map("map", { layers: [layerOsm] });
    map.setView(initial_position, initial_zoom)
    // Layer group
    const layerGroupAll = L.layerGroup().addTo(map);

    // Create custom circle pane to get popups before we hit the polygons
    const pane = map.createPane('circles');
    var baseMaps = {
        "OpenStreetMap": layerOsm
    };
    var overlayMaps = { "Pinp01nt 360": layerGroupAll }

    const layerControl = L.control.layers(baseMaps, overlayMaps).addTo(map);
} else {
    // const urlParams = new URLSearchParams(import.meta.url);
    let path_array = import.meta.url.split('map.js?')

    console.log('map init, path_array[0] = ' + path_array[0] + ', path_array[1] = ' + path_array[1]);
    console.log('map init, should init bounds here')
}


// Start with no overlays

// This calls into the cb_layer stuff 
async function render_all() {
  var zoom = map.getZoom()
  var boundsString = map.getBounds().toBBoxString()
  // console.log("render_all(), zoom level: " + zoom + ", boundsString = " + boundsString)
  cb_render_all(map, layerGroupAll, layerControl, zoom, boundsString);
}

// Catch our map-events, fetch data
map.on("moveend", render_all)

// This doesn't do what we want, causes multiple fires: map.on("load", render_all)

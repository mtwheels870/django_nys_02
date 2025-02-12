import { cb_render_all } from './cb_layer.js';

// Create the map
// export const map = L.map("map", { layers: [layerOsm] });

// Single global for the map
let global_map;

class MapWrapper {
    constructor() {
        console.log("constructor(), this.map = " + this.map);
        if (typeof global_map === 'undefined') {
            let osm = "https://www.openstreetmap.org/copyright";
            let copy = `© <a href='${osm}'>OpenStreetMap</a>`;
            let url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

            /* Create the attribution layer, is this added to the layer group 
               Ah, we use it below in the render_markers() */
            let layerOsm = L.tileLayer(url, { attribution: copy });
            let initial_position = [43.05, -76.1];
            let initial_zoom = 12.5
            console.log("creating initial map, map = " + global_map);
            global_map = L.map("map", { layers: [layerOsm] });
            global_map.setView(initial_position, initial_zoom);

            console.log("after create, map = " + global_map);
            // Layer group
            this.layerGroupAll = L.layerGroup().addTo(global_map);

            // Create custom circle pane to get popups before we hit the polygons
            let pane = global_map.createPane('circles');
            var baseMaps = {
                "OpenStreetMap": layerOsm
            };
            var overlayMaps = { "Pinp01nt 360": this.layerGroupAll }

            this.layerControl = L.control.layers(baseMaps, overlayMaps).addTo(global_map);
            console.log("after create, global_map = " + global_map);
        }
        this.map = global_map;
    }
}

export const map_wrapper = new MapWrapper()
console.log("after MapWrapper(), global_map = " + global_map);


// Start with no overlays

// This calls into the cb_layer stuff 
async function render_all() {
  var zoom = global_map.getZoom()
  var boundsString = global_map.getBounds().toBBoxString()
  // console.log("render_all(), zoom level: " + zoom + ", boundsString = " + boundsString)
  cb_render_all(zoom, boundsString);
}

// Catch our map-events, fetch data
global_map.on("moveend", render_all)

// This doesn't do what we want, causes multiple fires: map.on("load", render_all)

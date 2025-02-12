import { cb_render_all } from './cb_layer.js';

// Create the map
// export const map = L.map("map", { layers: [layerOsm] });

// Single global for the map
let global_map;

class MapWrapper {
    constructor() {
        if typeof global_map === 'undefined') {
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

            // Layer group
            this.layerGroupAll = L.layerGroup().addTo(map);

            // Create custom circle pane to get popups before we hit the polygons
            let pane = map.createPane('circles');
            var baseMaps = {
                "OpenStreetMap": layerOsm
            };
            var overlayMaps = { "Pinp01nt 360": layerGroupAll }

            this.layerControl = L.control.layers(baseMaps, overlayMaps).addTo(map);
            console.log("after create, global_map = " + global_map);
        }
        this.map = global_map;
    }
}

export const map_wrapper = MapWrapper()


// Start with no overlays

// This calls into the cb_layer stuff 
async function render_all() {
  var zoom = map.getZoom()
  var boundsString = map.getBounds().toBBoxString()
  // console.log("render_all(), zoom level: " + zoom + ", boundsString = " + boundsString)
  cb_render_all(zoom, boundsString);
}

// Catch our map-events, fetch data
map.on("moveend", render_all)

// This doesn't do what we want, causes multiple fires: map.on("load", render_all)

import { cb_render_all } from './cb_layer.js';

// Create the map
// export const map = L.map("map", { layers: [layerOsm] });

// Single global for the map
let global_map;

class MapWrapper {
    constructor() {
        // if (typeof window.maps === 'undefined') {
        console.log("MapWrapper(), checking global_map = " + global_map);
        // const urlParams = new URLSearchParams(window.location.search);
        if (typeof global_map === 'undefined') {
            let osm = "https://www.openstreetmap.org/copyright";
            let copy = `© <a href='${osm}'>OpenStreetMap</a>`;
            let url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

            /* Create the attribution layer, is this added to the layer group 
               Ah, we use it below in the render_markers() */
            let layerOsm = L.tileLayer(url, { attribution: copy });
            this.map = L.map("map", { layers: [layerOsm] });
            this.set_initial_position();

            // console.log("after create, map = " + global_map);
            // Layer group
            this.layerGroupAll = L.layerGroup().addTo(this.map);

            // Create custom circle pane to get popups before we hit the polygons
            let pane = this.map.createPane('circles');
            var baseMaps = {
                "OpenStreetMap": layerOsm
            };
            var overlayMaps = { "Pinp01nt 360": this.layerGroupAll }

            this.layerControl = L.control.layers(baseMaps, overlayMaps).addTo(this.map);

            // Save a reference in case we re-enter
            global_map = this.map;
            // console.log("after create, global_map = " + global_map);
        } else {
            console.log("map already exists = " + global_map + ", need to do more setup...");
            this.map = global_map;
        }
    }

    // Method doesn't take function 
    set_initial_position() {
        // Why doesn't this work?
        var urlParams = new URLSearchParams(import.meta.url);
        console.log("MapWrapper.s_i_p(), i.m.u = " + import.meta.url + ", urlParams = " + urlParams);

        // Split by hand
        var array = import.meta.url.split("map.js?");
        var length = array.length;
        console.log("MapWrapper.s_i_p(), length = " + length);
        if (length > 1) {
            var search_params = array[1];
            console.log("MapWrapper.s_i_p(), search_params = " + search_params );
            var single_float = "([+-]?([0-9]*[.])?[0-9]+)"
            var regexp_array = [single_float, single_float, single_float, single_float]
            var float_portion = regexp_array.join(",")
            var complete_regexp = "in_bbox=" + float_portion;
            console.log("MapWrapper.s_i_p(), complete_regexp = " + complete_regexp);
            var matches = search_params.match(complete_regexp);
            console.log("MapWrapper.s_i_p(), matches = " + matches);
        }
        let initial_position = [43.05, -76.1];
        let initial_zoom = 12.5
        this.map.setView(initial_position, initial_zoom);
    }
}

export const map_wrapper = new MapWrapper()
console.log("after MapWrapper(), global_map = " + global_map + ", this.map = " + map_wrapper.map);


// Start with no overlays

// This calls into the cb_layer stuff 
async function render_all() {
  var zoom = global_map.getZoom()
  var boundsString = global_map.getBounds().toBBoxString()
  // console.log("render_all(), zoom level: " + zoom + ", boundsString = " + boundsString)
  cb_render_all(map_wrapper, zoom, boundsString);
}

// Catch our map-events, fetch data
global_map.on("moveend", render_all)

// This doesn't do what we want, causes multiple fires: map.on("load", render_all)

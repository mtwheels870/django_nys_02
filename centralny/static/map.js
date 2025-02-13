import { cb_render_all } from './cb_layer.js';

// Create the map
// export const map = L.map("map", { layers: [layerOsm] });

// Single global for the map
let global_map;

class MapWrapper {
    constructor() {
        // if (typeof window.maps === 'undefined') {
        // console.log("MapWrapper(), checking global_map = " + global_map);
        // const urlParams = new URLSearchParams(window.location.search);
        if (typeof global_map === 'undefined') {
            let osm = "https://www.openstreetmap.org/copyright";
            let copy = `© <a href='${osm}'>OpenStreetMap</a>`;
            let url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

            /* Create the attribution layer, is this added to the layer group 
               Ah, we use it below in the render_markers() */
            let layerOsm = L.tileLayer(url, { attribution: copy });
            this.map = L.map("map", { layers: [layerOsm] });
            var call_render = this.set_initial_position();

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

            if (call_render) {
                // Explicitly call render_all()
                render_all();
            }
            // console.log("after create, global_map = " + global_map);
        } else {
            console.log("map already exists = " + global_map + ", need to do more setup...");
            this.map = global_map;
        }
    }

    // Method doesn't take function 
    set_initial_position() {
        // Why doesn't this work?
        // var urlParams = new URLSearchParams(import.meta.url);
        var found_bbox = false;
        // Split by hand
        var array = import.meta.url.split("map.js?");
        var length = array.length;
        if (length > 1) {
            var search_params = array[1];
            var single_float = "([+-]?[0-9]*[.]?[0-9]+)"
            var regexp_array = [single_float, single_float, single_float, single_float]
            var float_portion = regexp_array.join(",")
            var complete_regexp = "in_bbox=" + float_portion;
            var matches = search_params.match(complete_regexp);
            if (matches == null) {
                console.log("MapWrapper.s_i_p(), no regexp match, search_params = '" + search_params + "', ignoring...");
            } else {
                // matches[0] contains the entire matching string
                var floats_array = matches.slice(1).map(number => parseFloat(number));
                console.log("MapWrapper.s_i_p(), floats_array : " + floats_array);

                // Note coordinate swap here
                var corner1 = L.latLng(floats_array[1], floats_array[0]);
                var corner2 = L.latLng(floats_array[3], floats_array[2]);
                var bounds = L.latLngBounds(corner1, corner2)

                // Fit to those bounds
                this.map.fitBounds(bounds);

                found_bbox = true;
            }
        }
        if (!found_bbox) {
            // No vaild bounding box, set to our default
            let initial_position = [43.05, -76.1];
            let initial_zoom = 12.5
            this.map.setView(initial_position, initial_zoom);
        }
        return true;
    }
}

export const map_wrapper = new MapWrapper()
// console.log("after MapWrapper(), global_map = " + global_map + ", this.map = " + map_wrapper.map);


// Start with no overlays

// This calls into the cb_layer stuff 
async function render_all() {
  var zoom = global_map.getZoom()
  var boundsString = global_map.getBounds().toBBoxString()
  console.log("render_all(), zoom level: " + zoom + ", boundsString = " + boundsString)
  cb_render_all(map_wrapper, zoom, boundsString);
}

// Catch our map-events, fetch data
global_map.on("moveend", render_all)
global_map.on("load", () => {
    console.log("Map load");
});

// This doesn't do what we want, causes multiple fires: map.on("load", render_all)

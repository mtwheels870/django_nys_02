"use strict";

function get_file_picker_types(el) {
    var picker_names = {};
    $.each($(el).attr('class').split(' '), function(idx, class_name) {
        if (class_name.substr(0, 17) == 'file_picker_name_') {
            var type = class_name.split('_')[3];
            var name = class_name.split('_')[4];
            picker_names[type] = name;
        }
    });
    return picker_names;
}

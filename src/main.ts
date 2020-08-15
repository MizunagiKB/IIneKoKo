//npm install --save-dev @types/jquery
/// <reference types="jquery" />
//npm install --save-dev @types/semantic-ui
/// <reference types="semantic-ui" />
//npm install --save-dev @types/vue
/// <reference types="vue" />
//npm install --save-dev @types/fabric
/// <reference types="fabric" />

/// <reference path="async_request.ts" />

namespace iinekoko {

    const CANVAS_W = 512;
    const CANVAS_H = 512;
    const CANVAS_COLOR_BK = "#EFEFEF";
    const CANVAS_MARK_SIZE_MIN = 16;
    const CANVAS_MARK_SIZE_MAX = 256;
    const AUTO_UPDATE_TIME_MSEC = 3000;
    export const COLOR = { "R": "#FF0000", "G": "#00FF00", "B": "#0000FF" };

    export enum E_CANVAS_MODE {
        CANVAS_LST,
        CANVAS_NEW,
        CANVAS_MOD
    }

    var image_ref: string = "";
    export var o_iine_canvas: CIIneCanvas = null;
    var o_vue_image_ref_list = null;
    export var o_vue_menu_canvas_mod = null;

    class CIIneCanvas {
        o_canvas: fabric.Canvas;
        o_layerMod: fabric.Group = null;
        o_layerMrk: fabric.Group = null;
        o_layerRef: fabric.Group = null;
        o_reference_image: fabric.Image = null;
        b_mouse_press = false;
        active_shape = null;
        active_shape_axis_x = 0;
        active_shape_axis_y = 0;
        h_auto_update_timer = null;

        constructor(e_canvas_mode: E_CANVAS_MODE) {

            if (e_canvas_mode != E_CANVAS_MODE.CANVAS_LST) {
                const id_canvas = e_canvas_mode == E_CANVAS_MODE.CANVAS_NEW ? "id_canvas_new" : "id_canvas_mod";

                this.o_canvas = new fabric.Canvas(id_canvas, { selection: false });

                this.o_layerRef = new fabric.Group();
                this.o_layerMrk = new fabric.Group();
                this.o_layerMod = new fabric.Group();
                this.o_canvas.add(this.o_layerRef);
                this.o_canvas.add(this.o_layerMrk);
                this.o_canvas.add(this.o_layerMod);

                this.o_canvas.setBackgroundColor(CANVAS_COLOR_BK, function () { });
                this.o_canvas.isDrawingMode = false;
                this.o_canvas.renderAll();

                if (e_canvas_mode == E_CANVAS_MODE.CANVAS_MOD) {
                    this.o_canvas.on(
                        {
                            "mouse:down": function (o_evt) { o_iine_canvas.evt_mouse_down(o_evt); },
                            "mouse:up": function (o_evt) { o_iine_canvas.evt_mouse_up(o_evt); },
                            "mouse:move": function (o_evt) { o_iine_canvas.evt_mouse_move(o_evt); }
                        }
                    );
                }
            }

            $(".ccheck_view").hide();

            switch (e_canvas_mode) {
                case E_CANVAS_MODE.CANVAS_LST: $("#id_view_lst").show(); break;
                case E_CANVAS_MODE.CANVAS_NEW: $("#id_view_new").show(); break;
                case E_CANVAS_MODE.CANVAS_MOD: $("#id_view_mod").show(); break;
            }
        }

        set(o_image: fabric.Image): void {

            const f_scale_w = CANVAS_W / o_image.width;
            const f_scale_h = CANVAS_H / o_image.height;
            const f_scale = (f_scale_w > f_scale_h) ? f_scale_h : f_scale_w;

            o_image.selectable = false;
            o_image.scale(f_scale);

            this.o_layerRef.add(o_image);
            this.o_canvas.centerObject(o_image);

            this.o_reference_image = o_image;
        }

        to_json(): any {
            if (this.o_reference_image != null) {
                return this.o_reference_image.toJSON();
            } else {
                return null;
            }
        }

        order_auto_save() {
            this.h_auto_update_timer = window.setTimeout(
                function () { o_iine_canvas.evt_auto_save(); },
                AUTO_UPDATE_TIME_MSEC
            );
        }

        erase() {
            if (o_vue_menu_canvas_mod.desc_r.o_shape != null) {
                this.o_layerMod.remove(o_vue_menu_canvas_mod.desc_r.o_shape);
                o_vue_menu_canvas_mod.desc_r.o_shape = null;
            }
            if (o_vue_menu_canvas_mod.desc_g.o_shape != null) {
                this.o_layerMod.remove(o_vue_menu_canvas_mod.desc_g.o_shape);
                o_vue_menu_canvas_mod.desc_g.o_shape = null;
            }
            if (o_vue_menu_canvas_mod.desc_b.o_shape != null) {
                this.o_layerMod.remove(o_vue_menu_canvas_mod.desc_b.o_shape);
                o_vue_menu_canvas_mod.desc_b.o_shape = null;
            }

            this.order_auto_save();
        }

        evt_mouse_down(o_evt: any) {

            let item = null;

            switch (o_vue_menu_canvas_mod.active_desc) {
                case 0: item = o_vue_menu_canvas_mod.desc_r; break;
                case 1: item = o_vue_menu_canvas_mod.desc_g; break;
                case 2: item = o_vue_menu_canvas_mod.desc_b; break;
            }
            if (item == null) return;

            if (item.o_shape != null) {
                this.o_layerMod.remove(item.o_shape);
                item.o_shape = null;
            }

            this.active_shape_axis_x = o_evt.e.offsetX;
            this.active_shape_axis_y = o_evt.e.offsetY;

            item.o_shape = new fabric.Circle(
                {
                    radius: 1, fill: item.color, opacity: 0.5,
                    left: this.active_shape_axis_x,
                    top: this.active_shape_axis_y
                }
            );
            item.o_shape.radius = CANVAS_MARK_SIZE_MIN;

            item.o_shape.hasControls = false;
            item.o_shape.hasBorders = false;

            this.o_layerMod.add(item.o_shape);

            this.b_mouse_press = true;
        }

        evt_mouse_up(o_evt: any) {
            this.b_mouse_press = false;

            if (this.h_auto_update_timer != null) {
                window.clearTimeout(this.h_auto_update_timer);
                this.h_auto_update_timer = null;
            }

            this.order_auto_save();
        }

        evt_auto_save() {

            let list_mark = [];

            if (o_vue_menu_canvas_mod.desc_r.o_shape != null) {
                list_mark.push(
                    {
                        "name": "R",
                        "shape_type": "circle",
                        "radius": o_vue_menu_canvas_mod.desc_r.o_shape.radius,
                        "left": o_vue_menu_canvas_mod.desc_r.o_shape.left,
                        "top": o_vue_menu_canvas_mod.desc_r.o_shape.top
                    }
                );
            }
            if (o_vue_menu_canvas_mod.desc_g.o_shape != null) {
                list_mark.push(
                    {
                        "name": "G",
                        "shape_type": "circle",
                        "radius": o_vue_menu_canvas_mod.desc_g.o_shape.radius,
                        "left": o_vue_menu_canvas_mod.desc_g.o_shape.left,
                        "top": o_vue_menu_canvas_mod.desc_g.o_shape.top
                    }
                );
            }
            if (o_vue_menu_canvas_mod.desc_b.o_shape != null) {
                list_mark.push(
                    {
                        "name": "B",
                        "shape_type": "circle",
                        "radius": o_vue_menu_canvas_mod.desc_b.o_shape.radius,
                        "left": o_vue_menu_canvas_mod.desc_b.o_shape.left,
                        "top": o_vue_menu_canvas_mod.desc_b.o_shape.top
                    }
                );
            }

            let dict_param = {
                "id_image_ref": image_ref
            }

            let url = null;

            if (list_mark.length == 0) {
                url = "/api/remove_image_mrk";
            } else {
                url = "/api/append_image_mrk";
                dict_param["list_mark"] = list_mark;
            }

            $.ajax(
                {
                    url: url,
                    type: "POST",
                    data: JSON.stringify(dict_param),
                    cache: false,
                    contentType: false,
                    processData: false,
                    dataType: "json"
                }
            ).done(
                function (jsondata, status, o_xhr) {
                    console.log("OK");
                }
            ).fail(
                function (o_xhr, status, o_err) { console.log("NG"); }
            );
        }

        evt_mouse_move(o_evt: any) {

            if (this.b_mouse_press == true) {

                let item = null;
                const rX = Math.abs(this.active_shape_axis_x - o_evt.e.offsetX);
                const rY = Math.abs(this.active_shape_axis_y - o_evt.e.offsetY);
                const r = (rX > rY) ? rX : rY;

                switch (o_vue_menu_canvas_mod.active_desc) {
                    case 0: item = o_vue_menu_canvas_mod.desc_r; break;
                    case 1: item = o_vue_menu_canvas_mod.desc_g; break;
                    case 2: item = o_vue_menu_canvas_mod.desc_b; break;
                    default: item = null;
                }
                if (item == null) return;
                if (item.o_shape == null) return;

                item.o_shape.radius = Math.abs(Math.max(r, CANVAS_MARK_SIZE_MIN));

                this.o_canvas.renderAll();
            }
        }
    }

    function file_load(image_data: Blob) {
        const o_reader = new FileReader();

        //canvas_init("id_canvas_viewer");

        o_reader.onload = function (f) {
            const o_image = new Image();
            o_image.src = f.target.result as string;
            o_image.onload = function () {
                const o_reference_image = new fabric.Image(o_image);

                o_iine_canvas.set(o_reference_image);
            }
        }

        o_reader.readAsDataURL(image_data);
    }

    function evt_droparea_dragover(o_evt: any) {
        o_evt.stopPropagation();
        o_evt.preventDefault();
        o_evt.originalEvent.dataTransfer.dropEffect = "copy";
    }

    function evt_droparea_drop(o_evt: any) {
        o_evt.stopPropagation();
        o_evt.preventDefault();

        if (o_evt.originalEvent.dataTransfer.files.length == 1) {
            file_load(o_evt.originalEvent.dataTransfer.files[0]);
        }
    }

    function evt_btn_submit_file(o_evt: any) {

        const canvas_image_ref = o_iine_canvas.to_json();
        if (canvas_image_ref == null) { return; }

        let dict_param = {
            "title": $('input[name="text_title"]').val(),
            "desc_r": $('input[name="text_r"]').val(),
            "desc_g": $('input[name="text_g"]').val(),
            "desc_b": $('input[name="text_b"]').val(),
            "check_size": $('input[name="check_size"]:checked').val(),
            "image_ref": canvas_image_ref
        }

        const o_xhr = $.ajax(
            {
                url: "/api/new_image_ref",
                type: "POST",
                data: JSON.stringify(dict_param),
                cache: false,
                contentType: false,
                processData: false,
                dataType: "json"
            }
        );

        o_xhr.done(
            function (jsondata, status, o_xhr) {
                console.log("OK");
                view_change(E_CANVAS_MODE.CANVAS_MOD);
            }
        ).fail(
            function (o_xhr, status, o_err) { console.log("NG"); }
        );
    }

    function evt_btn_upload_file(o_evt: any) {
        if (o_evt.target.files.length == 1) {
            file_load(o_evt.target.files[0]);
        }
    }

    function get_url_param(): { [key: string]: string } {
        let list_result: { [key: string]: string } = {};
        let list_param: string[] = window.location.href.slice(window.location.href.indexOf("?") + 1).split("&");

        for (let n: number = 0; n < list_param.length; n++) {
            let listData: Array<string> = list_param[n].split("=");

            list_result[listData[0]] = listData[1];
        }

        return list_result;
    }

    function Base64ToImage(base64img, callback) {
        var img = new Image();
        img.onload = function () {
            callback(img);
        };
        img.src = base64img;
    }

    function view_reload() {
        $.ajax(
            {
                url: "/api/get_image_ref_list",
                type: "GET",
                data: {},
                dataType: "json",
                cache: false,
                contentType: false,
                processData: false
            }
        ).done(
            function (jsondata, status, o_xhr) {
                console.log("OK");
                for (let n: number = 0; n < jsondata.length; n++) {
                    const r = jsondata[n];
                    o_vue_image_ref_list.list_record.push({
                        "document_id": r.id,
                        "title": r.value.title,
                        "created_at": r.key[1]
                    });
                    console.log(jsondata[n]);
                }
            }
        ).fail(
            function (o_xhr, status, o_err) {
                console.log("NG");
            }
        );
    }

    export function view_change(e_mode: E_CANVAS_MODE) {
        o_iine_canvas = new CIIneCanvas(e_mode);
    }

    export function main() {
        const dict_param: { [key: string]: string } = get_url_param();
        image_ref = dict_param["image_ref"];

        $(".ui.radio.checkbox").checkbox();

        $("#id_file_droparea").on("dragover", evt_droparea_dragover);
        $("#id_file_droparea").on("drop", evt_droparea_drop);

        $("#id_btn_submit_file").on("click", evt_btn_submit_file);
        $("#id_btn_upload_file").on("change", evt_btn_upload_file);

        // menu
        new Vue({
            el: "#id_menu_image_lst",
            data: {
                name: "Vue.js"
            },
            methods: {
                evt_click: function (o_evt) {
                    view_change(E_CANVAS_MODE.CANVAS_LST);
                }
            }
        });
        new Vue({
            el: "#id_menu_image_new",
            methods: {
                evt_click: function (o_evt) { view_change(E_CANVAS_MODE.CANVAS_NEW); }
            }
        });

        console.log("xx3");
        o_vue_menu_canvas_mod = new Vue({
            el: "#id_menu_canvas_mod",
            data: {
                active_desc: null,
                title: "",
                visible_mod: true,
                visible_mrk: true,
                desc_r: { label: "", o_shape: null, color: "#FF0000", visible: true },
                desc_g: { label: "", o_shape: null, color: "#00FF00", visible: true },
                desc_b: { label: "", o_shape: null, color: "#0000FF", visible: true },
                list_record: []
            },
            methods: {
                evt_click_user: function () {
                    this.visible_mod = this.visible_mod == true ? false : true;
                    o_iine_canvas.o_layerMod.visible = this.visible_mod;
                    o_iine_canvas.o_canvas.renderAll();
                },
                evt_click_users: function () {
                    this.visible_mrk = this.visible_mrk == true ? false : true;
                    o_iine_canvas.o_layerMrk.visible = this.visible_mrk;
                    o_iine_canvas.o_canvas.renderAll();
                },
                evt_click_erase: function () { o_iine_canvas.erase(); },
                evt_click_delete: function () { },

                evt_click_r: function (o_evt) {
                    this.active_desc = 0;
                },
                evt_click_g: function (o_evt) {
                    this.active_desc = 1;
                },
                evt_click_b: function (o_evt) {
                    this.active_desc = 2;
                }
            }
        });

        o_vue_image_ref_list = new Vue({
            el: "#id_image_lst",
            data: {
                list_record: []
            }
        });

        view_reload();

        if (image_ref == null) {
            view_change(E_CANVAS_MODE.CANVAS_LST);
        } else {
            view_change(E_CANVAS_MODE.CANVAS_MOD);

            get_image_mrk(image_ref);
            get_image_mrk_list(image_ref);

            $.ajax(
                {
                    url: "/api/get_image_ref",
                    type: "POST",
                    data: JSON.stringify({ "document_id": image_ref }),
                    cache: false,
                    contentType: false,
                    processData: false,
                    dataType: "json"
                }
            ).done(
                function (jsondata, status, o_xhr) {
                    o_vue_menu_canvas_mod.title = jsondata["doc"].title;
                    for (let n = 0; n < jsondata["doc"].list_col_desc.length; n++) {
                        const item = jsondata["doc"].list_col_desc[n];
                        switch (item.name) {
                            case "R": o_vue_menu_canvas_mod.desc_r.label = item.value; break;
                            case "G": o_vue_menu_canvas_mod.desc_g.label = item.value; break;
                            case "B": o_vue_menu_canvas_mod.desc_b.label = item.value; break;
                        }
                    }

                    Base64ToImage(jsondata["ref"], function (o_image) {
                        const o_reference_image = new fabric.Image(o_image);
                        o_iine_canvas.set(o_reference_image);
                    });
                }
            ).fail(
                function (o_xhr, status, o_err) { console.log("NG"); }
            );
        }
    }
}

// [EOF]

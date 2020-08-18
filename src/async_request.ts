//npm install --save-dev @types/jquery
/// <reference types="jquery" />
//npm install --save-dev @types/semantic-ui
/// <reference types="semantic-ui" />
//npm install --save-dev @types/vue
/// <reference types="vue" />
//npm install --save-dev @types/fabric
/// <reference types="fabric" />

/// <reference path="main.ts" />


namespace iinekoko {

    export function del_image_ref(image_ref: string, url: string) {
        $.ajax(
            {
                url: "/api/del_image_ref/" + image_ref,
                type: "POST",
                data: {},
                dataType: "json",
                cache: false,
                contentType: false,
                processData: false
            }
        ).done(
            function (jsondata, status, o_xhr) {
                location.href = url;
            }
        ).fail(
            function (o_xhr, status, o_err) {
            }
        );
    }

    export function get_image_mrk(image_ref: string) {
        $.ajax(
            {
                url: "/api/get_image_mrk/" + image_ref,
                type: "POST",
                data: {},
                dataType: "json",
                cache: false,
                contentType: false,
                processData: false
            }
        ).done(
            function (jsondata, status, o_xhr) {

                if (jsondata != null) {
                    const f_alpha = 0.5;
                    const item = jsondata["doc"];

                    if (item != null) {
                        const list_mark = [item.mark_r, item.mark_g, item.mark_b];

                        for (let n = 0; n < list_mark.length; n++) {
                            const mark = list_mark[n];
                            if (mark != null) {
                                let o_shape = new fabric.Circle({
                                    radius: 1,
                                    fill: COLOR[n],
                                    opacity: f_alpha,
                                    left: mark.left,
                                    top: mark.top
                                });
                                o_shape.radius = mark.radius;
                                o_iine_canvas.o_layerMod.add(o_shape);

                                switch (n) {
                                    case 0: o_vue_menu_canvas_mod.desc_r.o_shape = o_shape; break;
                                    case 1: o_vue_menu_canvas_mod.desc_g.o_shape = o_shape; break;
                                    case 2: o_vue_menu_canvas_mod.desc_b.o_shape = o_shape; break;
                                }
                            }
                        }
                    }
                }
            }
        ).fail(
            function (o_xhr, status, o_err) {
            }
        );
    }

    export function get_image_mrk_list(image_ref: string) {
        $.ajax(
            {
                url: "/api/get_image_mrk_list/" + image_ref,
                type: "POST",
                data: {},
                dataType: "json",
                cache: false,
                contentType: false,
                processData: false
            }
        ).done(
            function (jsondata, status, o_xhr) {

                const f_alpha = jsondata.length == 0 ? 0.5 : 0.5 / jsondata.length;

                for (let i = 0; i < jsondata.length; i++) {
                    const item_key = jsondata[i].key;
                    const item = jsondata[i].value;
                    const list_mark = [item.mark_r, item.mark_g, item.mark_b];

                    for (let j = 0; j < list_mark.length; j++) {
                        const mark = list_mark[j];
                        if (mark != null) {
                            let o_shape = new fabric.Circle({
                                radius: 1,
                                fill: COLOR[mark.name],
                                opacity: f_alpha,
                                left: mark.left,
                                top: mark.top
                            });
                            o_shape.radius = mark.radius;
                            o_iine_canvas.o_layerMrk.add(o_shape);
                        }
                    }
                    o_vue_menu_canvas_mod.list_record.push({ "username": item.tw_username, "created_at": item_key[1] });
                }
                o_iine_canvas.o_canvas.renderAll();
            }
        ).fail(
            function (o_xhr, status, o_err) {
            }
        );
    }
}


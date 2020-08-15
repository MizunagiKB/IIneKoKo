//npm install --save-dev @types/jquery
/// <reference types="jquery" />
//npm install --save-dev @types/semantic-ui
/// <reference types="semantic-ui" />
//npm install --save-dev @types/vue
/// <reference types="vue" />
//npm install --save-dev @types/fabric
/// <reference types="fabric" />
/// <reference path="main.ts" />
var iinekoko;
(function (iinekoko) {
    function get_image_mrk(image_ref) {
        $.ajax({
            url: "/api/get_image_mrk",
            type: "POST",
            data: JSON.stringify({ "id_image_ref": image_ref }),
            dataType: "json",
            cache: false,
            contentType: false,
            processData: false
        }).done(function (jsondata, status, o_xhr) {
            const f_alpha = 0.5;
            const item = jsondata["doc"];
            if (item != null) {
                for (let j = 0; j < item.list_mark.length; j++) {
                    const mark = item.list_mark[j];
                    let o_shape = new fabric.Circle({
                        radius: 1,
                        fill: iinekoko.COLOR[mark.name],
                        opacity: f_alpha,
                        left: mark.left,
                        top: mark.top
                    });
                    o_shape.radius = mark.radius;
                    iinekoko.o_iine_canvas.o_layerMod.add(o_shape);
                    switch (mark.name) {
                        case "R":
                            iinekoko.o_vue_menu_canvas_mod.desc_r.o_shape = o_shape;
                            break;
                        case "G":
                            iinekoko.o_vue_menu_canvas_mod.desc_g.o_shape = o_shape;
                            break;
                        case "B":
                            iinekoko.o_vue_menu_canvas_mod.desc_b.o_shape = o_shape;
                            break;
                    }
                }
            }
        }).fail(function (o_xhr, status, o_err) {
        });
    }
    iinekoko.get_image_mrk = get_image_mrk;
    function get_image_mrk_list(image_ref) {
        $.ajax({
            url: "/api/get_image_mrk_list",
            type: "POST",
            data: JSON.stringify({ "id_image_ref": image_ref }),
            dataType: "json",
            cache: false,
            contentType: false,
            processData: false
        }).done(function (jsondata, status, o_xhr) {
            const f_alpha = jsondata.length == 0 ? 0.5 : 0.5 / jsondata.length;
            for (let i = 0; i < jsondata.length; i++) {
                const item_key = jsondata[i].key;
                const item = jsondata[i].value;
                for (let j = 0; j < item.list_mark.length; j++) {
                    const mark = item.list_mark[j];
                    let o_shape = new fabric.Circle({
                        radius: 1,
                        fill: iinekoko.COLOR[mark.name],
                        opacity: f_alpha,
                        left: mark.left,
                        top: mark.top
                    });
                    o_shape.radius = mark.radius;
                    iinekoko.o_iine_canvas.o_layerMrk.add(o_shape);
                }
                iinekoko.o_vue_menu_canvas_mod.list_record.push({ "username": item.tw_username, "created_at": item_key[1] });
            }
            iinekoko.o_iine_canvas.o_canvas.renderAll();
        }).fail(function (o_xhr, status, o_err) {
        });
    }
    iinekoko.get_image_mrk_list = get_image_mrk_list;
})(iinekoko || (iinekoko = {}));
//# sourceMappingURL=async_request.js.map
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function () {
    $(".release_form").submit(function (e) {
        e.preventDefault()
        // 发布新闻
        $(this).ajaxSubmit({
            beforeSubmit: function (request) {
                // 在提交之前，对参数进行处理
                for(var i=0; i<request.length; i++) {
                    var item = request[i];
                    if (item["name"] == "content") {
                        // 获取编辑器里面的内容
                        item["value"] = tinyMCE.activeEditor.getContent()
                    }
                }
            },
            url: "/user/news_release",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 选中索引为6的左边单菜单
                    window.parent.fnChangeMenu(6)
                    // 滚动到顶部
                    window.parent.scrollTo(0, 0)
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})

// $(function () {
// //
// //     $(".release_form").submit(function (e) {
// //         e.preventDefault()
// //
// //         // TODO 发布完毕之后需要选中我的发布新闻
// //         var params = {}
// //
// //         $(this).serializeArray().map(function (x) {
// //             params[x.name] = x.value;
// //         });
// //
// //         for(var i=0; i<request.length; i++) {
// //                     var item = params[i];
// //                     if (item["name"] == "content") {
// //                         item["value"] = tinyMCE.activeEditor.getContent()
// //                     }
// //                 }
// //
// //         $.ajax({
// //             url:'/user/new_release',
// //             method:'POST',
// //             headers:{
// //                 'X_CSRFToken':getCookie('csrf_token')
// //             },
// //             contentType:'application/json',
// //             data:JSON.stringify(params),
// //             success:function (resp) {
// //                 if (resp.erron == '0'){
// //                     window.parent.fnChangeMenu(6)
// //                     window.parent.scrollTo(0, 0)
// //                 }
// //                 else {
// //                     alert(resp.errmsg)
// //                 }
// //             }
// //         })
// //         // // 选中索引为6的左边单菜单
// //         //
// //         // // 滚动到顶部
// //         // window.parent.scrollTo(0, 0)
// //     })
// // })
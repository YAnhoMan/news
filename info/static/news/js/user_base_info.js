function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function () {

    $(".base_info").submit(function (e) {
        e.preventDefault()

        var signature = $("#signature").val()
        var nick_name = $("#nick_name").val()
        var gender = $('input:radio[name="gender"]:checked').val();


        if (!nick_name) {
            alert('请输入昵称')
            return
        }
        if (!gender) {
            alert('请选择性别')
        }

        // TODO 修改用户信息接口
        $.ajax({
            url:'/user/user_info',
            contentType:'application/json',
            type:'POST',
            headers:{
                'X_CSRFToken':getCookie('csrf_token')
            },
            data:JSON.stringify({
                'nick_name': nick_name,
                'signature': signature,
                'gender': gender
            }),
            success:function (resp) {
                if (resp.errno == '0'){
                    alert(resp.errmsg);
                    $('.user_center_name', parent.document).html(nick_name);
                    $('a[href="/user/info"]', parent.document).html(nick_name);
                    $('.input_sub').blur()
                }
                else {
                    alert(resp.errmsg);
                }
            }
        })

    })
})
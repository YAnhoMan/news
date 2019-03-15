function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function updateCommentCount() {
    var count = $('.comment_list').length;
    $('.comment_count').html(count + '条评论');
}


$(function(){

    // 打开登录框
    $('.comment_form_logout').click(function () {
        $('.login_form_con').show();
    })

    // 收藏
    $(".collection").click(function () {
        $.ajax({
            url:'/news/new_collect',
            type:'POST',
            contentType:'application/json',
            headers:{
                'X-CSRFToken': getCookie('csrf_token')
            },
            data:JSON.stringify({
                'news_id':$('.collection').attr('data-newid'),
                'action': 'collect'
            })
                ,
            success:function (resp) {
                if (resp.errno == '0') {
                    $('.collection').hide();
                    $('.collected').show();
                }
                else if(resp.errno == "4101"){
                    $('.login_form_con').show()
                }
                else {
                    alert(resp.errmsg);
                }

            }
        })
       
    })

    // 取消收藏
    $(".collected").click(function () {
        $.ajax({
            url:'/news/new_collect',
            type:'POST',
            contentType:'application/json',
            headers:{
                'X-CSRFToken': getCookie('csrf_token')
            },
            data:JSON.stringify({
                'news_id':$('.collection').attr('data-newid'),
                'action': 'cancel_collect'
            }),
            success:function (resp) {
                if (resp.errno == '0') {
                    $('.collected').hide();
                    $('.collection').show();
                }
                else if(resp.errno == "4101"){
                    $('.login_form_con').show()
                }
                else {
                    alert(resp.errmsg);
                }

            }
        })

     
    })

        // 评论提交
    $(".comment_form").submit(function (e) {
        e.preventDefault();

        var input_comment = $('.comment_input').val();

        if (!input_comment){
            alert('请输入评论内容!')
        }

        $.ajax({
            url:'/news/new_comment',
            type:'POST',
            contentType:'application/json',
            headers:{
                'X-CSRFToken':getCookie('csrf_token')
            },
            data:JSON.stringify({
                'news_id':$('.collection').attr('data-newsid'),
                'content':input_comment,
            }),
            success:function (resp) {
                if (resp.errno == "0"){
                //    失去焦点并清空数据
                    $('.comment_input').blur();
                    $('.comment_input').val("");

                //增加新内容
                    var comment_html = '';

                    var comment = resp.data;

                    comment_html += '<div class="comment_list">'
                    comment_html += '<div class="person_pic fl">'

                    if (comment.user.avatar_url) {
                        comment_html += '<img src="' + comment.user.avatar_url + '" alt="用户图标">'
                    }
                    else {
                        comment_html += '<img src="../static/news/images/person01.png" alt="用户图标">'
                    }
                    comment_html += '</div>'
                    comment_html += '<div class="user_name fl">' + comment.user.nick_name + '</div>'
                    comment_html += '<div class="comment_text fl">'
                    comment_html += comment.content
                    comment_html += '</div>'
                    comment_html += '<div class="comment_time fl">' + comment.create_time + '</div>'

                    comment_html += '<a href="javascript:;" class="comment_up fr" data-commentid="' + comment.id + '" data-newsid="' + comment.news_id + '" data-likecount="0">赞</a>'
                    comment_html += '<a href="javascript:;" class="comment_reply fr">回复</a>'
                    comment_html += '<form class="reply_form fl" data-commentid="' + comment.id + '" data-newsid="' + comment.news_id + '">'
                    comment_html += '<textarea class="reply_input"></textarea>'
                    comment_html += '<input type="button" value="回复" class="reply_sub fr">'
                    comment_html += '<input type="reset" name="" value="取消" class="reply_cancel fr">'
                    comment_html += '</form>'

                    comment_html += '</div>'

                //增加新内容
                    $('.comment_list_con').prepend(comment_html)
                    updateCommentCount()
                }
            }
        })

    })

    $('.comment_list_con').delegate('a,input','click',function(){

        var sHandler = $(this).prop('class');

        if(sHandler.indexOf('comment_reply')>=0)
        {
            $(this).next().toggle();
        }

        if(sHandler.indexOf('reply_cancel')>=0)
        {
            $(this).parent().toggle();
        }

        if(sHandler.indexOf('comment_up')>=0)
        {
            var $this = $(this);
            var action = 'add';
            if(sHandler.indexOf('has_comment_up')>=0)
            {
                // 如果当前该评论已经是点赞状态，再次点击会进行到此代码块内，代表要取消点赞
                action = 'remove';
                // $this.removeClass('has_comment_up')
            }

            var comment_id = $this.attr('data-commentid');
            var data_like_count = parseInt($this.attr('data-likecount'));
            
            $.ajax({
                url:'/news/comment_like',
                contentType:'application/json',
                type:'POST',
                headers:{
                    'X-CSRFToken': getCookie('csrf_token')
                },
                data:JSON.stringify({
                    'comment_id': comment_id,
                    'action': action
                }),
                success:function (resp) {
                    if (resp.errno == '4101'){
                        $('.login_form_con').show();
                    }
                    else if (resp.errno == '0') {
                        if (action == 'add'){
                            $this.addClass('has_comment_up');
                            data_like_count += 1
                        }
                        else {
                            $this.removeClass('has_comment_up');
                            data_like_count -= 1
                        }
                        $this.attr('data-likecount', data_like_count);
                        if (data_like_count == 0){
                            $this.html('赞')
                        }
                        else {
                            $this.html(String(data_like_count))
                        }
                    }
                    else {
                        alert(resp.errmsg)
                    }
                }
            })


        }

        if(sHandler.indexOf('reply_sub')>=0)
        {
            var $this = $(this);
            var input_area = $this.parent();
            var content = $this.prev().val();

            if (!content){
                alert('请输入回复评论内容')
            }

            $.ajax({
            url:'/news/new_comment',
            type:'POST',
            contentType:'application/json',
            headers:{
                'X-CSRFToken':getCookie('csrf_token')
            },
            data:JSON.stringify({
                'news_id':input_area.attr('data-newsid'),
                'content':content,
                'parent_id': input_area.attr('data-commentid')
            }),
            success:function (resp) {
                if (resp.errno == "0"){
                //    失去焦点并清空数据
                    $this.prev().blur();
                    $this.prev().val("");
                    $this.parent().hide();

                    //增加新内容
                    var comment = resp.data;
                    // 拼接内容
                    var comment_html = "";
                    comment_html += '<div class="comment_list">';
                    comment_html += '<div class="person_pic fl">';
                    if (comment.user.avatar_url) {
                        comment_html += '<img src="' + comment.user.avatar_url + '" alt="用户图标">'
                    }else {
                        comment_html += '<img src="../static/news/images/person01.png" alt="用户图标">'
                    }
                    comment_html += '</div>'
                    comment_html += '<div class="user_name fl">' + comment.user.nick_name + '</div>'
                    comment_html += '<div class="comment_text fl">'
                    comment_html += comment.content
                    comment_html += '</div>'
                    comment_html += '<div class="reply_text_con fl">'
                    comment_html += '<div class="user_name2">' + comment.parent.user.nick_name + '</div>'
                    comment_html += '<div class="reply_text">'
                    comment_html += comment.parent.content
                    comment_html += '</div>'
                    comment_html += '</div>'
                    comment_html += '<div class="comment_time fl">' + comment.create_time + '</div>'

                    comment_html += '<a href="javascript:;" class="comment_up fr" data-commentid="' + comment.id + '" data-newsid="' + comment.news_id + '" data-likecount="0">赞</a>'
                    comment_html += '<a href="javascript:;" class="comment_reply fr">回复</a>'
                    comment_html += '<form class="reply_form fl" data-commentid="' + comment.id + '" data-newsid="' + comment.news_id + '">'
                    comment_html += '<textarea class="reply_input"></textarea>'
                    comment_html += '<input type="button" value="回复" class="reply_sub fr">'
                    comment_html += '<input type="reset" name="" value="取消" class="reply_cancel fr">'
                    comment_html += '</form>'

                    comment_html += '</div>'

                //增加新内容
                    $('.comment_list_con').prepend(comment_html);
                //评论条数加1
                    updateCommentCount()
                }
            }
        })

        }
    })

        // 关注当前新闻作者
    $(".focus").click(function () {

    })

    // 取消关注当前新闻作者
    $(".focused").click(function () {

    })
})
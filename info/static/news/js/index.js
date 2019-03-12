var currentCid = 1; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
// 定义标志位
var data_querying = false;   // 是否正在向后台获取数据 false没有往后台请求数据


$(function () {

    // 注意： 请求新闻列表数据
    updateNewsData()


    // 首页分类切换
    $('.menu li').click(function () {
        var clickCid = $(this).attr('data-cid')
        $('.menu li').each(function () {
            $(this).removeClass('active')
        })
        $(this).addClass('active')

        // 表示点击别的分类了
        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid

            // 重置分页参数
            cur_page = 1
            total_page = 1
            updateNewsData()
        }
    })

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100) {
            // TODO 判断页数，去更新新闻数据
            // console.log("来了，老弟！！")
            // 会请求多次，限定请求次数
            // data_querying=false 没有人往后端请求数据，我可以向后端请求数据
            if(!data_querying){
                // 当前页码小于等于总页数
               if(cur_page <= total_page){
                    // 往后端请求数据
                    data_querying = true
                    updateNewsData()
               }else{
                   // 页码超标
                   data_querying = false
               }

            }


        }
    })
})

// 请求首页新闻列表数据
function updateNewsData() {

    var params = {
        "page": cur_page,
        "cid": currentCid,
    }
    $.get("/news_list",
        params,
        function (resp) {
        if (resp) {

            // 只有第一次请求的时候才需要清空数据
            if (cur_page == 1){
                // 先清空原有数据
                $(".list_con").html('')

            }

            // 总页数赋值
            total_page = resp.data.total_page

            // 请求下一页数据 页码累加
            cur_page += 1

            // 当数据加载完毕，需要将data_querying设置为false，方便下次请求下一页数据
            data_querying = false

            // 显示数据
            for (var i=0;i<resp.data.news_dict_list.length;i++) {
                var news = resp.data.news_dict_list[i]
                var content = '<li>'
                content += '<a href="news/' + news.id + '" class="news_pic fl"><img src="' + news.index_image_url + '?imageView2/1/w/170/h/170"></a>'
                content += '<a href="news/' + news.id + '" class="news_title fl">' + news.title + '</a>'
                content += '<a href="news/' + news.id + '" class="news_detail fl">' + news.digest + '</a>'
                content += '<div class="author_info fl">'
                content += '<div class="source fl">来源：' + news.source + '</div>'
                content += '<div class="time fl">' + news.create_time + '</div>'
                content += '</div>'
                content += '</li>'

                // 添加新闻数据到ul标签中
                $(".list_con").append(content)
            }
        }
    })
}

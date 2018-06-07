
$(function(){
	(function(){
	    var x,y,endX,endY;

	    var rectx,recty,rectendx,rectendy;
	    //undo redo
		var history =new Array();

		var cStep = -1;
		var rectTip = $(" <div style='border:1px solid gray;width:1px;height:1px;position:absolute;display:none;'></div>");
		$("#container").append(rectTip);
		var flag = false;
		var ctx=document.getElementById("myCanvas").getContext("2d");
		var command = 1;
		var commandCallbacks = $.Callbacks();
		commandCallbacks.add(switchCanvasContext);
		commandCallbacks.add(switchCursorStyle);
		// By default,
		$("#tools_pencil").trigger("click");

		commandCallbacks.fire(command);
		initUI();
		  // command emitter
		$("[name='tools']").change(function(){
			var val = $(this).val();
			var type = $(this).attr("id");
				switch(type){
					case "tools_pencil"		:{command=1;break;}
					case "tools_trash"		:{command=2;break;}
					case "tools_rectangle"	:{command=3;break;}
					default 				:{command=1;}
				}
				  //initialize canvas context and cursor style
				commandCallbacks.fire(command);
			//}
		});

		$("#container").mousemove(mouseMoveEventHandler);
		function mouseMoveEventHandler(e){
			switch(command){
				case 1	:	{	drawPencil(e);break; }
				case 3	:	{   fakeRectangleInput(e);break;    }
			}
		}

		function drawPencil(e){
			if(flag){
				var offset = $("#myCanvas").offset();
				var x = e.pageX-offset.left;
				var y = e.pageY-offset.top;
				ctx.lineTo(x,y);
				ctx.stroke();
			}
			else {
				// set the begin path for brash
				ctx.beginPath();
				var offset = $("#myCanvas").offset();
				var x = e.pageX-offset.left;
				var y = e.pageY-offset.top;
				ctx.moveTo(x,y);
			}
		}

		function fakeRectangleInput(e){
		    var offset = $("#myCanvas").offset();
            endX= e.pageX-offset.left;
            endY  = e.pageY-offset.top;
            var borderWidth  = $("#penWidth").val();
            if(flag){
               rectTip.css({left:x,top:y});
               rectTip.width(endX-x-borderWidth*2);
               rectTip.height(endY-y-borderWidth*2);
               console.log(flag);
            }
		}


		function clearCanvas() {
			var width  = $("#myCanvas").attr("width");
			var height  = $("#myCanvas").attr("height");
			ctx.clearRect(0,0,width,height);
		}


		$("#container").mousedown(function(e){
				// set mousedown flag for mousemove event
			flag=true;
			//set the begin path of the brash
			var offset = $("#myCanvas").offset();
			x = e.pageX-offset.left;
			y = e.pageY-offset.top;

			switch(command){
				case 1	:	{	break; }
				case 3	:	{
                    var borderColor = "#"+ $("#colorpicker-popup").val();
                    var borderWidth  = $("#penWidth").val()+"px";
                    var sr = borderColor +" "+borderWidth+ " solid";
                    var backgroundColor ="#"+$("#colorpicker-popup2").val();
                    rectTip.css({
                        "border": sr,
                        "background-color":backgroundColor
                    });
                    rectTip.show();
                    break;
                }
			}
		});

		$("#container").mouseup(function(e){
			flag=false;
			historyPush();
			switch(command){
				case 1	:	{	break; }
				case 3	:	{   drawRectangle();break;}
			}
		});


		$("#tools_undo").click(undo);
		$("#tools_redo").click(redo);

		function undo(){
			if (cStep >= 0){
				clearCanvas();
				cStep--;
				var tempImage = new Image();
				tempImage.src = history[cStep];
				tempImage.onload = function () { ctx.drawImage(tempImage, 0, 0);};
			}
		}

		function redo(){
			if (cStep <history.length-1){
				clearCanvas();
				cStep++;
				var tempImage = new Image();
				tempImage.src = history[cStep];
				tempImage.onload = function () { ctx.drawImage(tempImage, 0, 0); };
			}
		}

		function drawRectangle(){
		    var borderWidth  = $("#penWidth").val();
		    ctx.strokeRect(x,y,endX-x,endY-y);
		    rectx=x;
		    rectendx=endX;
            recty=y;
		    rectendy=endY;
		    $("#myCanvas").focus();
		    rectTip.hide();
        }

		  //// define function
		function initUI(){
								  //界面UI初始化，对话框
			$( "#dialog" ).dialog({
				autoOpen: true,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close").hide();
				},
				resizable:false,
				draggable:false,
				height:800,
				width:870,
				position: {
					my: 'center',
					at: 'center',
					of: window
				}
			});
			$("#tools_rectangle").button({
                icons:{
                   primary:"ui-icon-stop"
                }
			});
			$("#tools_process").click(function () {

                var imgData = document.getElementById("myCanvas").toDataURL("image/png");


                $.ajax({
					url : "/colorize/colorizer",
					type : 'post',
					async: true,//使用同步的方式,true为异步方式
					data : {image : imgData,left:parseFloat(rectx),right:parseFloat(rectendx),up:parseFloat(recty),down:parseFloat(rectendy)},//这里使用json对象
					success : function(data){
						if(data.code==404){
							alert("请先加载图片！");
						}
						else {
							putImg('resImg', data.img64);
						}
					},
					fail:function(){
						alert("error");
					}
                });
                //timerId=window.setInterval(getProgress,200);

            });

			function getProgress(){
            //使用JQuery从后台获取JSON格式的数据
				$.ajax({
					type:"get",//请求方式
				   	url:"/colorize/colorizer",//发送请求地址
				   	timeout:30000,//超时时间：30秒
				   	dataType:"json",//设置返回数据的格式
					async:true,
				   	//请求成功后的回调函数 data为json格式
				   	success:function(data){
						if(data.progress>=100){
							window.clearInterval(timerId);
				   		}
				   		var p = $('#progress_colorize').parent().width();
				   		var res=p*data.progress/100;
					   	$('#progress_colorize').width(res);
				  	},
				  	//请求出错的处理
				  	error:function(){
						window.clearInterval(timerId);
						alert("请求出错");
				  	}
			   	});
			}

			$("#tools_save").click(function () {
				$.post("/save/colorizer",function (data) {
					if(data.code==200){
						alert("保存成功！");
					}
					else{
						alert("保存失败！");
					}
				})
			});
			  //3. 工具条
			$("#tools_pencil").button({
				icons:{
					primary:"ui-icon-pencil"
				}
			});


			$("#tools_trash").button({
				icons:{
					primary:"ui-icon-trash"
				}
			});

			$("#tools_save").button({
				icons:{
					primary:"ui-icon-disk"
				}
			});

			$("#tools_process").button({
				icons:{
					primary:"ui-icon-seek-end"
				}
			});

			$("#tools_undo").button({
				icons:{
					primary:"ui-icon-arrowreturnthick-1-w"
				}
			});

			$("#tools_redo").button({
				icons:{
				   primary:"ui-icon-arrowreturnthick-1-e"
				}
			});


            $('input[name="file"]').fileupload({
                url: '/upload',
                Type: "POST",
                autoUpload: true,
                acceptFileTypes:/\.(jpg|jpeg)$/i,// 文件格式
                maxFileSize: 99 * 1024 * 1024, //文件大小
                dataType:"json",
                // 设置验证失败的提示信息
                messages: {
                    maxFileSize: 'File exceeds maximum allowed size of 99MB',
                    acceptFileTypes: 'File type not allowed'
                },
                done: function(e,data) {
                    $.get("/files",function(data){
                    	putResRawImgs(data.img64);
                    });
                },
                fail: function() {
                    alert("s");
                     // 上传失败的回调函数，可以弹出“上传失败”之类的弹框
                }
            });
			  //4. 画笔粗细设置
			$("#penWidth").selectmenu({
				width:100,
				select:penWidthEventListener
			});

			function penWidthEventListener(event,ui){
				var lineWidth = ui.item.value;
				ctx.lineWidth =lineWidth;
				return false;
			}

			  //5. 颜色选择器
			$("#colorpicker-popup").colorpicker({
				buttonColorize: true,
				alpha:          true,
				draggable:       true,
				showOn:         'both',
				close:borderColorEventListener
			});

			function borderColorEventListener(e){
				  // 1. set brash context
				var color= "#"+$(this).val();
				ctx.strokeStyle =color;
			}


		}
		function historyPush(){
			cStep++;
			if (cStep < history.length) {
				history.length = cStep;
			}
			history.push($("#myCanvas").get(0).toDataURL());
		}


		function switchCanvasContext(command){
			ctx.lineWidth = $("#penWidth").val();
			ctx.strokeStyle ="#ffffff";//+ $("#colorpicker-popup").val();
			ctx.lineCap = "round";
			if(command){
				switch(command){
					case 1: {
						break;
					}
					case 2:{
						clearCanvas();
						$("#tools_pencil").trigger("click");
						$("#tools_pencil").focus();
					}
				}
			}
			return ctx;
		}

		function switchCursorStyle(command) {
			switch(command){
				default:{
					$("#myCanvas").addClass("container_pencil");
					break;
				}
			}
		}
   })();
	function putResRawImgs(base){ // 将[resImg,rawImg]显示出来
		putImg('rawImg',base);
		putImg('resImg',base);
	}
	function putImg (id, base){  //将base64 img 放到#id中
		var img = '<img width=400px height=400px src="data:image/png;base64,'+base+'" class="inline"/> ';
		$('#'+id).html(img);
	}
});
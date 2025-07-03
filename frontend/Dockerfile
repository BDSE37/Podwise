# 使用 Nginx 作為基礎映像
FROM nginx:alpine

# 複製靜態檔案
COPY . /usr/share/nginx/html/

# 複製 nginx 設定檔
COPY nginx-default.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 啟動 Nginx
CMD ["nginx", "-g", "daemon off;"] 
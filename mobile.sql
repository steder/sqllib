--
-- mobile.sql
--
-- a bunch mobile queries
--

[get_design]
select productId, artistId, userId, mediaId, medias, title, designedby from productId = $1

[get_designs]
select productId, artistId, userId, mediaId, medias, title, designedby from product where visible = true order by productId desc limit $1 offset $2

[get_design_info]
select name, username from users where userId = $1

[get_high_quality_image_for_products]
select max(width), max(height), filename from images where product_id in ($1) and style = 'design'



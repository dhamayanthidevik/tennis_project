
use tennis_db;
-- -------------------------------------------------------------
-- --------------Competitions + categories----------------------
-- -------------------------------------------------------------
-- 1.List all competitions along with their category name -------------------------------- 
select com.competition_id,
       com.competition_name,
       com.`type`,
       com.gender,
       ca.category_name
  from Competitions com 
  left join categories ca 
  on com.category_id=ca.category_id;
-- 2.Count the number of competitions in each category-------------------------
select ca.category_name,com.category_id,count(*) as no_competition
		from competitions com 
        left join categories ca 
        on  com.category_id=ca.category_id
        group by com.category_id,ca.category_name
        order by no_competition desc;
-- 3. Find all competitions of type 'doubles'-----------
select com.competition_id,com.competition_name,com.`type`,com.gender,ca.category_name 
              from competitions com 
              left join categories ca 
              on com.category_id=ca.category_id 
              where type='doubles';
-- 4. Get competitions that belong to a specific category (e.g., ITF Men)----------
select ca.category_name,com.category_id,com.competition_name,com.type,com.gender 
          from categories ca inner join competitions com
          on ca.category_id=com.category_id where ca.category_name='ITF Men';
-- 5.Identify parent competitions and their sub-competitions---------------
select *from competitions;
select p.parent_id As parent_id,
	   p.competition_name as parent_name,
       c.competition_id as sub_competition_id,
       c.competition_name as sub_competition_name
       from competitions p
       left join competitions c
       on p.parent_id=c.parent_id
       order by p.competition_id;
-- 6.Analyze the distribution of competition types by category----
select ca.category_name,com.type,count(*) as no_competition
from competitions com 
left join categories ca 
on com.category_id=ca.category_id 
group by com.type,category_name
order by ca.category_name,no_competition;
-- 7.List all competitions with no parent (top-level competitions)----
select competition_id,competition_name,type,gender
from competitions 
where parent_id is null ;
-- -------------------------------------------------------------------------------- 
--  ------------------------------- Complexes +venues------------------------------
-- --------------------------------------------------------------------------------
-- 1.List all venues along with their associated complex name------------------
select v.venue_id,v.venue_name,v.city_id,v.city_name,v.country_name,v.country_code,v.timezone,c.complex_name
	   from venues v left join  complexes c 
       on v.complex_id=c.complex_id;
-- 2.Count the number of venues in each complex-------------------------
select c.complex_id,c.complex_name,count(v.venue_id) as count_venue
from complexes c
left join venues v
on c.complex_id=v.complex_id
group by c.complex_name,c.complex_id;

-- 3. Get details of venues in a specific country (e.g., Chile)---------
select *from venues where country_name='chile';
-- 4.Identify all venues and their timezones---------
select venue_name,city_id,city_name,country_name,country_code,timezone from venues;
-- 5.Find complexes that have more than one venue----------
select c.complex_id,c.complex_name,count(v.venue_id) as count_venue
 from complexes c join venues v 
 on c.complex_id=v.complex_id 
 group by c.complex_name,c.complex_id
 having count(v.venue_id) > 1
 order by count_venue desc;
 -- 6.List venues grouped by country-------
 select country_name,count(venue_id) as count_venue  
 from venues 
 group by country_name
 order by count_venue desc;
 -- 7.Find all venues for a specific complex (e.g., Nacional)----
 select v.venue_id,v.venue_name,v.city_id,v.city_name,v.country_name,v.country_code,v.timezone,c.complex_name
  from venues v left join complexes c 
  on v.complex_id=c.complex_id 
  where complex_name like '% Nacional%' or complex_name like 'Nacional%';
-- -------------------------------------------------------------------------------- 
--  ------------------------------- Competitor_Rankings + Competitors--------------
-- --------------------------------------------------------------------------------
-- 1.Get all competitors with their rank and points.------------------------------ 
 select c.name,cr.rank,cr.points 
 from competitors c
 left join competitor_rankings cr
 on c.competitor_id=cr.competitor_id
 order by cr.rank;
 -- 2.Find competitors ranked in the top 5------
 select c.name,cr.`rank`,cr.points 
 from competitors c
 left join competitor_rankings cr
 on c.competitor_id=cr.competitor_id
 order by cr.`rank`
 limit 5;
 -- 3.List competitors with no rank movement (stable rank)------
 select c.name,cr.`rank`,cr.`movement`
 from competitor_rankings cr
 left join competitors c
 on cr.competitor_id=c.competitor_id
 where cr.movement=0
  order by cr.`rank`;
 -- 4. Get the total points of competitors from a specific country (e.g., Croatia)--
select c.country,sum(points) as tol_points
from competitor_rankings cr
left join competitors c
on cr.competitor_id=c.competitor_id
where country='Croatia'
group by c.country;
-- 5.Count the number of competitors per country---
select c.country,count(distinct cr.competitor_id) as competitor_count
from competitor_rankings cr
left join competitors c
on cr.competitor_id=c.competitor_id
group by c.country 
order by competitor_count desc;
-- 6.Find competitors with the highest points in the current week---- 
select *from competitor_rankings where week =42 limit 5;
 where week=42;

 


 
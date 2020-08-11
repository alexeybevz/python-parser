-- 1. ���������� �� ����� ������ ��������� ������ ����� �������� �� �����?
select u.country, COUNT(ua.id)
from Users u
left join UserAction ua ON ua.userId = u.id
group by u.country
order by COUNT(ua.id) desc

-- 2. ���������� �� ����� ������ ���� ����� ������������ �������� �� ��������� �fresh_fish�?
select ISNULL(u.country, '-') as country, COUNT(ua.id)
from Users u
left join UserAction ua ON ua.userId = u.id
where ua.action like '%fresh_fish%'
group by ISNULL(u.country, '-')
order by COUNT(ua.id) desc

-- 3. � ����� ����� ����� ���� ����� ������������� ��������� �frozen_fish�?
;with pre AS (
select
case
	when cast(actionDate as time) between '00:00:01' and '06:00:00' then '����'
	when cast(actionDate as time) between '06:00:00' and '12:00:00' then '����'
	when cast(actionDate as time) between '12:00:00' and '18:00:00' then '����'
	when cast(actionDate as time) between '18:00:00' and '23:59:59' then '�����'
end as dt
from UserAction
where action like '%frozen_fish%'
)
select dt, COUNT(dt) as cnt
from pre
group by dt
order by COUNT(dt) desc

-- 4. ����� ������������ ����� �������� �� ���� �� ��������������� ��� (c 00 ����� 00 ������ �� 59 ����� 59 ������)?
select cast(actionDate as date), DATEPART(Hour, actionDate), count(actionDate) as cnt
from UserAction
group by cast(actionDate as date), DATEPART(Hour, actionDate)
order by count(actionDate) desc

-- 5. ������ �� ����� ��������� ���� ����� �������� ��������� � ������� �� ��������� �semi_manufactures�?
;with cart_with_semi_manufactures as (
	select distinct c.cartId
	from CartItem c
	inner join Good g ON g.id = c.goodId
	where g.category = 'semi_manufactures'
)
select g.category, count(c.cartId) as cnt
from cart_with_semi_manufactures csm
inner join CartItem c ON c.cartId = csm.cartId
inner join Good g ON g.id = c.goodId
where g.category <> 'semi_manufactures'
group by g.category
order by count(c.cartId) desc

-- 6. ������� ��������� (�� ����������) ������ �������?
select count(distinct id)
from Cart
where payDate is NULL

-- 7. ����� ���������� ������������� ��������� ��������� �������?
WITH pre AS (
    SELECT u.id, COUNT(c.id) AS cnt
    FROM Users u
    LEFT JOIN Cart c ON c.userId = u.id
                    AND c.payDate IS NOT NULL
    GROUP BY u.id
    HAVING COUNT(c.id) > 1
) SELECT COUNT(id) FROM pre
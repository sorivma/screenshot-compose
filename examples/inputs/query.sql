select
  users.id,
  users.email,
  count(events.id) as event_count
from users
left join events on events.user_id = users.id
where users.active = true
group by users.id, users.email
order by event_count desc
limit 10;

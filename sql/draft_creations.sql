SELECT DISTINCT
  creation.wiki,
  creation.event_revId as first_rev_id, 
  creation.event_pageId as page_id, 
  creation.event_title as title, 
  creation.timestamp as created 
FROM staging.page_creation_enwiki_201503 creation 
INNER JOIN PageMove_7495717 move USING (wiki, event_pageId) 
WHERE wiki = "enwiki" AND
  creation.event_namespace IN (0, 118) OR 
  (move.event_oldNamespace NOT IN (0, 118) AND 
   move.event_newNamespace in (0, 118));

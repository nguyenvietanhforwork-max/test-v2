-- Optional dev seed: a few entities and one example news item.
insert into entities (name, type, country, industry) values
  ('Vingroup', 'company', 'VN', 'real-estate'),
  ('Novaland', 'company', 'VN', 'real-estate'),
  ('VinFast', 'company', 'VN', 'automotive'),
  ('Petrolimex', 'company', 'VN', 'energy'),
  ('real-estate', 'industry', null, null),
  ('automotive', 'industry', null, null),
  ('energy', 'industry', null, null)
on conflict do nothing;

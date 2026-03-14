# Seed data for testing

Dummy data in CSV and Excel for the המחלץ app.

## Files

| File | Use |
|------|-----|
| **volunteers_seed.csv** / **volunteers_seed.xlsx** | Reference list of volunteers. Add them manually via Admin → ניהול מתנדבים → הוסף מתנדב, or use for import if you add a bulk-import feature. Columns: first_name, last_name, phone, group_tag, living_area. |
| **residents_seed.csv** / **residents_seed.xlsx** | For **event resident upload**. Create an event, then in the event flow use "העלאת רשימת תושבים" and upload one of these files. Columns (Hebrew): שם פרטי, שם משפחה, כתובת, טלפון, הערות. |

## Regenerating Excel from CSV

If you edit the CSV files, regenerate the Excel files:

```bash
cd backend
python -m scripts.generate_seed_excel
```

This overwrites `volunteers_seed.xlsx` and `residents_seed.xlsx` in `seed_data/`.

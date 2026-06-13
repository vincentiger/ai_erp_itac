# Template Storage Deployment Notes

## Standard path

Templates are standardized under the project uploads folder:

`C:\ai_erp_itac\uploads\templates`

The backend resolves template files from:

- `FORMS_UPLOAD_DIR` in `.env`
- then the `templates` subfolder under that base path

Effective runtime path:

`<FORMS_UPLOAD_DIR>\templates\<docx_name>`

## Official setting

Use this `.env` value on the current machine and on the customer machine:

```env
FORMS_UPLOAD_DIR=C:\ai_erp_itac\uploads
```

This keeps templates inside the project area for easier maintenance, backup, and migration.

## Important rule

The folder name must be `templates` (plural), not `template`.

The current backend code uses:

- `uploads/templates`
- `uploads/instances`
- `uploads/exports`

If the folder is named `template`, template lookup will fail.

## Database storage rule

`dbo.myTemplate.docx_path` should store only the file name, for example:

`LQP-08-01.docx`

This avoids machine-specific absolute paths and makes migration safer.

## Deployment note

IIS does not need to serve or read these template files directly.

So the templates should stay in:

`C:\ai_erp_itac\uploads\templates`

There is no need to place them under:

`C:\inetpub\wwwroot\newweb2021\uploads\templates`

## Suggested checklist

1. Keep the template files in `C:\ai_erp_itac\uploads\templates`.
2. Make sure `.env` contains `FORMS_UPLOAD_DIR=C:\ai_erp_itac\uploads`.
3. When moving to another machine, copy the whole `uploads` folder or at least the `templates` subfolder.
4. Restart the backend after changing `.env`.

# GitHub Actions Setup

Este repositorio usa GitHub Actions para desplegar automáticamente a AWS Lambda cuando se hace push a `main`.

## Configuración de Secrets

Añade estos secrets en tu repositorio de GitHub:
**Settings > Secrets and variables > Actions > New repository secret**

### Secrets requeridos:

1. **AWS_ACCESS_KEY_ID**
   - Tu AWS Access Key ID
   - Obtener en: AWS Console > IAM > Users > Security credentials

2. **AWS_SECRET_ACCESS_KEY**
   - Tu AWS Secret Access Key
   - Se genera junto con el Access Key ID

### Permisos IAM requeridos:

El usuario IAM debe tener una política con estos permisos:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction"
      ],
      "Resource": "arn:aws:lambda:eu-north-1:561903439674:function:pagamipana-ocr-python"
    }
  ]
}
```

## Workflow

El workflow se ejecuta automáticamente cuando:
- Se hace `push` a la rama `main`

Pasos del workflow:
1. ✅ Checkout del código
2. 🔐 Configurar credenciales AWS
3. 🐳 Login a ECR
4. 🏗️ Build de imagen Docker
5. ⬆️ Push a ECR con tags `latest` y `<commit-sha>`
6. 🚀 Actualizar función Lambda
7. ⏳ Esperar a que la actualización complete

## Monitoreo

Ver el progreso en: **Actions** tab del repositorio

## Testing local

Para probar localmente antes de hacer push:

```bash
./build_python.sh
```

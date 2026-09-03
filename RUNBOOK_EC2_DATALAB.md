# Runbook — EC2 interna de prueba PySpark en DataLab

Guía para levantar la instancia de cómputo Spark **dentro** de la cuenta DataLab
(`107094296911`), en subnet **privada** (sin acceso a internet). Complementa el
botón "☁️ Probar en EC2 (interno)" de la pestaña Data Redactada.

> Contexto: DataLab está bajo AWS Control Tower. No hay VPC default, ni Internet
> Gateway, ni NAT, ni endpoints SSM. Todas las subredes son privadas. Por eso esta
> instancia **no es pública**: solo se alcanza desde la red del banco / VPN a su IP
> privada. La instalación de PySpark se hace vía S3 (hay un VPC endpoint S3), no por
> internet.

---

## 0. Datos del entorno (verificados)

- Cuenta DataLab: `107094296911` (perfil AWS local `datalab`)
- Región: `us-east-1`
- VPC: `vpc-0a4538a2c855cd628` (aws-controltower-VPC, `172.31.0.0/16`)
- Subredes privadas (elegir una, p.ej. AZ us-east-1a):
  - `subnet-03b6e15f482a814d6` (us-east-1a)
  - `subnet-0ad90c49d097e5b11` (us-east-1b)
  - `subnet-0d1ff00bc3d09bfd6` (us-east-1a)
- VPC endpoint S3 (Gateway): disponible → permite `aws s3 cp` sin internet
- Bucket de trabajo existente: `datalake-bnx-scripts-dev`

---

## 1. Requisitos que debe habilitar el equipo de DataLab / redes

Estos NO los puede crear el usuario `benjamin.garcia` (IAM restringido). Solicitar:

1. **IAM instance profile** para la EC2 con la policy administrada
   `AmazonSSMManagedInstanceCore` + lectura del bucket `datalake-bnx-scripts-dev`.
   (SSM permite administrarla sin SSH ni IP pública — ver punto 2.)
2. **Una de estas dos vías de conexión** (elegir según lo que el banco permita):
   - **(preferida) Endpoints SSM** en la VPC: `com.amazonaws.us-east-1.ssm`,
     `com.amazonaws.us-east-1.ssmmessages`, `com.amazonaws.us-east-1.ec2messages`
     (tipo Interface, en la subnet privada, con SG que permita 443 interno).
     Con esto se administra por Session Manager sin abrir nada a internet.
   - **(alternativa) Acceso por VPN/Direct Connect** del banco a la IP privada,
     y una key pair para SSH (importar `monkey2` — ver punto 3).

Sin al menos una de las dos, la instancia queda inalcanzable.

---

## 2. Instalar PySpark sin internet (vía S3)

Desde una máquina con perfil `datalab` y acceso al bucket:

```bash
# 1. Descargar los binarios una vez (donde SÍ haya internet) y subirlos a S3
#    - openjdk 17 (tar.gz), Spark 3.5.1 (spark-3.5.1-bin-hadoop3.tgz)
#    - (opcional) un wheelhouse de pip: pyspark, py4j
aws s3 cp corretto-17.tar.gz         s3://datalake-bnx-scripts-dev/bootstrap/ --profile datalab
aws s3 cp spark-3.5.1-bin-hadoop3.tgz s3://datalake-bnx-scripts-dev/bootstrap/ --profile datalab
aws s3 cp app-bundle.tar.gz          s3://datalake-bnx-scripts-dev/bootstrap/ --profile datalab
# app-bundle.tar.gz = el repo (sin .git ni zips), para no depender de GitHub
```

En la EC2 (por SSM o SSH), el user-data / bootstrap baja todo del endpoint S3:

```bash
aws s3 cp s3://datalake-bnx-scripts-dev/bootstrap/ /opt/bootstrap/ --recursive
# instalar java, spark, python; desempacar el app-bundle en /home/ec2-user/app
```

---

## 3. Lanzar la instancia (cómputo grande para Spark)

```bash
# (si se usa SSH) importar la MISMA llave monkey2 a DataLab
ssh-keygen -y -f /Users/benjamingarcia/Documents/llaves/monkey2.pem > /tmp/monkey2.pub
aws ec2 import-key-pair --key-name monkey2 \
  --public-key-material fileb:///tmp/monkey2.pub \
  --region us-east-1 --profile datalab

# Security group interno: SOLO tráfico dentro de la VPC (no 0.0.0.0/0)
aws ec2 create-security-group --group-name bnx-spark-internal \
  --description "BNX Spark interno DataLab" \
  --vpc-id vpc-0a4538a2c855cd628 --region us-east-1 --profile datalab
# permitir 8081 (UI/API) y 22 (SSH) SOLO desde el CIDR de la VPC:
aws ec2 authorize-security-group-ingress --group-id <SG_ID> \
  --protocol tcp --port 8081 --cidr 172.31.0.0/16 --region us-east-1 --profile datalab
aws ec2 authorize-security-group-ingress --group-id <SG_ID> \
  --protocol tcp --port 22   --cidr 172.31.0.0/16 --region us-east-1 --profile datalab

# Instancia: c5.4xlarge = 16 vCPU / 32 GB (más cores para Spark).
# Alternativas con más RAM: r5.4xlarge (16 vCPU/128 GB) o c5.9xlarge (36 vCPU).
aws ec2 run-instances \
  --image-id <AMI_AL2023_de_DataLab> \
  --instance-type c5.4xlarge \
  --key-name monkey2 \
  --iam-instance-profile Name=<INSTANCE_PROFILE_con_SSM> \
  --security-group-ids <SG_ID> \
  --subnet-id subnet-03b6e15f482a814d6 \
  --no-associate-public-ip-address \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=bnx-spark-internal}]' \
  --region us-east-1 --profile datalab
```

> `--no-associate-public-ip-address`: es interna a propósito.
> Obtener la AMI AL2023 vigente en DataLab con:
> `aws ssm get-parameters --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --region us-east-1 --profile datalab --query 'Parameters[0].Value' --output text`

---

## 4. Servicio (idéntico a como corre en local)

`serve_ui.py` sirve UI + API en el puerto 8081. Como servicio systemd:

```ini
# /etc/systemd/system/bnx.service
[Unit]
Description=BNX Convertidor (UI + API + Spark local)
After=network.target
[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/app
ExecStart=/usr/bin/python3 serve_ui.py
Restart=always
Environment=PYSPARK_PYTHON=/usr/bin/python3
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now bnx
sudo systemctl status bnx
```

---

## 5. Conectar el botón de la UI

En la pestaña **Data Redactada** → engranaje **⚙️** junto a los botones de prueba:
pegar la **IP privada** de la instancia con el puerto, p.ej. `http://172.31.x.x:8081`,
y **Guardar** (se persiste en el navegador). A partir de ahí, el botón
**"☁️ Probar en EC2 (interno)"** enruta la prueba a esa instancia. El botón
**"💻 Probar local"** sigue corriendo en la máquina de cada persona.

> Solo funciona desde una máquina en la red del banco / VPN que alcance esa IP privada.

---

## 6. Notas

- La instancia es interna: no se expone por CloudFront ni a internet.
- Para "todos por internet" seguir usando el despliegue de la cuenta monkey
  (o pedir a redes una subnet pública/ALB autorizado en DataLab).
- Tamaño sugerido `c5.4xlarge` (16 vCPU). Con `serve_ui.py`, Spark usa `local[*]`
  y `spark.sql.shuffle.partitions=8`, así que aprovecha todos los cores.

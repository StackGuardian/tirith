img_name := "stackguardian-docs"
timestamp := $(shell date +%s)
img_nonprod_name_timestamp := 790543352839.dkr.ecr.eu-central-1.amazonaws.com/$(img_name):$(timestamp)
img_nonprod_tag_latest := 790543352839.dkr.ecr.eu-central-1.amazonaws.com/$(img_name):latest
build-ship-docker-image-qa:
	docker build --tag $(img_nonprod_name_timestamp) .
	docker tag $(img_nonprod_name_timestamp) ${img_nonprod_tag_latest}
	aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 790543352839.dkr.ecr.eu-central-1.amazonaws.com
	docker push $(img_nonprod_name_timestamp)
	docker push ${img_nonprod_tag_latest}

deploy-latest-image-ec2-qa: build-ship-docker-image-qa
	# ssh -o StrictHostKeyChecking=accept-new -i .secrets/nonprod-euc1.pem ec2-user@10.0.0.54 \
	# 	'aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 790543352839.dkr.ecr.eu-central-1.amazonaws.com \
	# 	&& docker stop docs || true \
	# 	&& docker rm docs || true \
	# 	&& docker run --restart=always -d --name docs -p 80:80 $(img_nonprod_name_timestamp) \
	# 	&& docker logs -f docs'
	aws ecs update-service --cluster platform-services --service docs --force-new-deployment

docker-logs-ec2-qa:
	ssh -o StrictHostKeyChecking=accept-new -i .secrets/nonprod-euc1.pem ec2-user@10.0.0.54 'docker logs -f docs'

img_prod_name_timestamp := 476299211833.dkr.ecr.eu-central-1.amazonaws.com/$(img_name):$(timestamp)-prod
img_prod_tag_latest := 476299211833.dkr.ecr.eu-central-1.amazonaws.com/$(img_name):latest
build-ship-docker-image-prod:
	aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 476299211833.dkr.ecr.eu-central-1.amazonaws.com
	docker build --tag $(img_prod_name_timestamp) .
	docker push $(img_prod_name_timestamp)

deploy-latest-image-ec2-prod: build-ship-docker-image-prod
	ssh -o StrictHostKeyChecking=accept-new -i .secrets/sg-platform-prod.pem ec2-user@172.24.36.90 \
		'aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 476299211833.dkr.ecr.eu-central-1.amazonaws.com \
		&& docker stop docs || true \
		&& docker rm docs || true \
		&& docker run --restart=always -d --name docs -p 80:80 $(img_prod_name_timestamp) \
		&& docker logs -f docs'
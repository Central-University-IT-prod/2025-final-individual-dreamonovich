import os
from yandex_cloud_ml_sdk import YCloudML


def generate_advertising_text(title, targeting=None):
    instruction = "Ты — профессиональный маркетолог с опытом написания высококонверсионной рекламы. Для генерации рекламного текста ты изучаешь потенциальную целевую аудиторию и оптимизируешь рекламный текст так, чтобы он обращался именно к этой целевой аудитории. Напиши рекламный текст для следующих продуктов/услуг. Создай текст до 300 символов объявления с привлекающим внимание заголовком и убедительным призывом к действию, который побуждает пользователей к целевому действию."

    prompt = f"Продукт/услуга: {title}. "
    if targeting:
        prompt += f"Целевая аудитория: {targeting}."

    messages = [
        {"role": "system", "text": instruction},
        {"role": "user", "text": prompt},
    ]

    sdk = YCloudML(
        folder_id="b1gd9iki2060shcc9st8",
        auth=os.environ.get(
            "YANDEX_API_TOKEN", "REDACTED"
        ),
    )

    model = sdk.models.completions("yandexgpt-lite")
    result = model.configure(temperature=0).run(messages)

    return result.alternatives[0].text

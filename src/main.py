from ai.auth import client


def main():
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Who you are? Please introduce yourself in 100 words.",
            }
        ],
        model="gemini-2.0-flash",
    )
    print(chat_completion.choices[0].message.content)


if __name__ == "__main__":
    main()

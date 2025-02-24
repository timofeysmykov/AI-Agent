from setuptools import setup, find_packages

setup(
    name="ai_assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.32.0",
        "anthropic>=0.28.0",
        "httpx>=0.27.0",
        "python-dotenv>=1.0.1",
        "requests>=2.31.0"
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "ai_assistant": ["prompts/*"],
    },
) 
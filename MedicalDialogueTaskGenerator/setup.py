"""
医学对话任务生成器安装配置
Medical Dialogue Task Generator Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="medical-dialogue-task-generator",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="一个可复用的医学对话任务生成器",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/MedicalDialogueTaskGenerator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "medical-task-generator=src.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    zip_safe=False,
    keywords="medical dialogue task generator ai evaluation healthcare",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/MedicalDialogueTaskGenerator/issues",
        "Source": "https://github.com/yourusername/MedicalDialogueTaskGenerator",
        "Documentation": "https://github.com/yourusername/MedicalDialogueTaskGenerator/docs",
    },
)

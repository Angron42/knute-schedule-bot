# pylint: disable=wrong-import-position

"""
Script for loading teachers to csv file.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import csv

import progressbar

from lib.teacher_loader import get_faculties, get_teachers
from lib.teacher_loader.schemas import Teacher


def load_teachers_to_file(filepath: str):
    """Load teachers to csv file"""
    _load_teachers_to_file(filepath, _load_teachers())


def _load_teachers() -> list[Teacher]:
    """Load teachers from site"""

    teachers = []
    faculties = get_faculties()
    print(f'Faculties: {len(faculties)}')

    for faculty in faculties:
        bar = progressbar.ProgressBar(max_value=len(faculty.chairs))
        for chair in bar(faculty.chairs):
            teachers.extend(get_teachers(chair.page_link))

    return teachers


def _load_teachers_to_file(filepath: str, teachers: list[Teacher]):
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['name', 'description', 'photo_link', 'page_link'])

        for teacher in teachers:
            writer.writerow([teacher.name.lower(), teacher.description,
                             teacher.photo_link, teacher.page_link])


def main():
    """Main function"""

    os.environ.setdefault('CACHE_PATH', 'cache')
    filepath = os.path.join(os.getenv('CACHE_PATH'), 'teachers.csv')
    load_teachers_to_file(filepath)


if __name__ == '__main__':
    main()
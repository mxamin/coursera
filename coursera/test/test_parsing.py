#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test functionality of coursera module.
"""
import json
import os.path
import pytest

from six import iteritems
from mock import patch, Mock, mock_open

from coursera import coursera_dl


# JSon Handling

@pytest.fixture
def get_page(monkeypatch):
    monkeypatch.setattr(coursera_dl, 'get_page', Mock())


@pytest.fixture
def json_path():
    return os.path.join(os.path.dirname(__file__), "fixtures", "json")


def test_that_should_not_dl_if_file_exist(get_page, json_path):
    coursera_dl.get_page = Mock()
    coursera_dl.download_about(object(), "matrix-002", json_path)
    assert coursera_dl.get_page.called is False


def test_that_we_parse_and_write_json_correctly(get_page, json_path):

    raw_data = open(os.path.join(os.path.dirname(__file__), "fixtures", "json", "unprocessed.json")).read()
    coursera_dl.get_page = lambda x, y: raw_data
    open_mock = mock_open()

    with patch('coursera.coursera_dl.open', open_mock, create=True):

        coursera_dl.download_about(object(), "networksonline-002", json_path)

    open_mock.assert_called_once_with(os.path.join(json_path, 'networksonline-002-about.json'), 'w')

    data = json.loads(open_mock().write.call_args[0][0])

    assert data['id'] == 394
    assert data['shortName'] == 'networksonline'


# Test Syllabus Parsing

@pytest.fixture
def get_video(monkeypatch):
    """
    mock some methods that would, otherwise, create
    repeateadly many web requests.

    More specifically, we mock:

    * the search for hidden videos
    * the actual download of videos
    """

    # Mock coursera_dl.grab_hidden_video_url
    monkeypatch.setattr(coursera_dl, 'grab_hidden_video_url',
                        lambda session, href: None)

    # Mock coursera_dl.get_video
    monkeypatch.setattr(coursera_dl, 'get_video',
                        lambda session, href: None)

    # Mock coursera_dl.get_on_demand_video_url
    monkeypatch.setattr(coursera_dl, 'get_on_demand_video_url',
                        lambda session, video_id: {'mp4': '{video_id}.mp4'.format(video_id=video_id),
                                                   'srt': '{video_id}.srt'.format(video_id=video_id)})


@pytest.mark.parametrize(
    "filename,num_sections,num_lectures,num_resources,num_videos", [
        ("regular-syllabus.html", 23, 102, 502, 102),
        ("links-to-wikipedia.html", 5, 37, 158, 36),
        ("preview.html", 20, 106, 106, 106),
        ("sections-not-to-be-missed.html", 9, 61, 224, 61),
        ("sections-not-to-be-missed-2.html", 20, 121, 397, 121),
        ("parsing-datasci-001-with-bs4.html", 10, 97, 358, 97),  # issue 134
        ("parsing-startup-001-with-bs4.html", 4, 44, 136, 44),  # issue 137
        ("parsing-wealthofnations-001-with-bs4.html", 8, 74, 296, 74),  # issue 131
        ("parsing-malsoftware-001-with-bs4.html", 3, 18, 56, 16),  # issue 148
        ("multiple-resources-with-the-same-format.html", 18, 97, 478, 97),
    ]
)
def test_parse(get_video, filename, num_sections, num_lectures, num_resources, num_videos):
    filename = os.path.join(
        os.path.dirname(__file__), "fixtures", "html",
        filename)

    with open(filename) as syllabus:
        syllabus_page = syllabus.read()

        sections = coursera_dl.parse_syllabus(None, syllabus_page, None)

        # section count
        assert len(sections) == num_sections

        # lecture count
        lectures = [lec for sec in sections for lec in sec[1]]
        assert len(lectures) == num_lectures

        # resource count
        resources = [(res[0], len(res[1]))
                     for lec in lectures for res in iteritems(lec[1])]
        assert sum(r for f, r in resources) == num_resources

        # mp4 count
        assert sum(r for f, r in resources if f == "mp4") == num_videos


@pytest.mark.parametrize(
    'filename, num_modules, num_sections, num_lectures, num_resources, num_videos',
    [
        ('regular-on-demand-syllabus-calculus1.json', 16, 79, 193, 386, 193),
    ]
)
def test_parse_on_demand(get_video, filename, num_modules, num_sections,
                         num_lectures, num_resources, num_videos):
    """
    Parse syllabus of on-demand courses.
    """

    syllabus_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'json',
                                 filename)

    with open(syllabus_file) as syllabus:
        syllabus_page = syllabus.read()

        modules = coursera_dl.parse_on_demand_syllabus(None, syllabus_page)
        with open('calculus1_syllabus', 'w') as hd:
            hd.write(str(modules).encode('utf-8'))

        # module count
        assert len(modules) == num_modules

        # section count
        sections = [sec for m in modules for sec in m[1]]
        assert len(sections) == num_sections

        # lecture count
        lectures = [lec for sec in sections for lec in sec[1]]
        assert len(lectures) == num_lectures

        # resource count
        resources = [(res[0], len(res[1]))
                     for lec in lectures for res in iteritems(lec[1])]
        assert sum(r for f, r in resources) == num_resources

        # video count
        assert sum(r for f, r in resources if f == 'mp4') == num_videos

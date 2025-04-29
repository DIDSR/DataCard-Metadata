.. dcard-completeness documentation master file, created by
   sphinx-quickstart on Tue Apr 29 09:14:23 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

dcard-completeness documentation
================================

.. Add your content using ``reStructuredText`` syntax. See the
.. `reStructuredText <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
.. documentation for details.

Functions
=========

**Score Utils**
----------------

.. autofunction:: score_utils.dataset_level_completeness_check
----

.. autofunction:: score_utils.compute_completeness_score
----

.. autofunction:: score_utils.record_level_completeness_check
----


**Field Matching Utils**
-------------------------

.. autofunction:: field_matching_utils.clean_string
----

.. autofunction:: field_matching_utils.strict_field_matching
----

.. autofunction:: field_matching_utils.soft_field_matching
----

.. autofunction:: field_matching_utils.dictionary_field_matching
----

.. autofunction:: field_matching_utils.fuzzy_field_matching
----

.. autofunction:: field_matching_utils.get_fuzzy_matches
----

.. autofunction:: field_matching_utils.get_LM_matches
----

.. autofunction:: field_matching_utils.ranked_field_matching
----


**IO Utils**
---------------

.. autofunction:: io_utils.load_metadata_file
----

.. autofunction:: io_utils.load_dataset_csv
----

.. autofunction:: io_utils.load_json
----

.. autofunction:: io_utils.load_dataset_xls
----

.. autofunction:: io_utils.get_field_item
----

.. autofunction:: io_utils.get_dictionary
----

.. autofunction:: io_utils.find_key_path
----

.. autofunction:: io_utils.plot_completeness_barchart
----

.. autofunction:: io_utils.add_text_sbarchart
----



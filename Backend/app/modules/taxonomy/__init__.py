"""``taxonomy`` 模块 —— 分类 + 标签 + 文章-标签关系。

旧职责（``TECHNICAL_ARCHITECTURE.md`` §5.5）::

    taxonomy | 分类 + 标签 + 文章-标签关系
             | article_categories / article_tags / article_tag_relations
             | /admin/articleCategory · /admin/article/tag
               /blog/articleCategory · /blog/article/tag

Stage 2.2 实现范围：分类与标签的 CRUD + 两个 blog 端只读端点 + 按标签分页。
"""

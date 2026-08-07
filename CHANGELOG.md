# 1.0.0 (2026-08-07)


### Features

* initial marketplace release ([4a6652e](https://github.com/Web3-Plurality/plurality-market-ai-service/commit/4a6652ee97b9710051d626bfacd592ef872bbd75))

## [1.20.2](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.20.1...v1.20.2) (2026-02-19)


### Bug Fixes

* **release:** split docker build into prepare and publish steps ([6986a7f](https://github.com/Web3-Plurality/plurality-ai-service/commit/6986a7f5375056d8b139593dd7cfcbfda1f7f203))

## [1.20.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.20.0...v1.20.1) (2026-02-19)


### Bug Fixes

* **workflows:** adds disk cleanup step ([a992c5c](https://github.com/Web3-Plurality/plurality-ai-service/commit/a992c5c0f34216699f4fd7e025180c9cee05afcb))

# [1.20.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.19.2...v1.20.0) (2026-02-19)


### Features

* **context:** add pagination to get_context_data endpoint ([15485c2](https://github.com/Web3-Plurality/plurality-ai-service/commit/15485c232b0a8d3c4074444a76a4cc28d5e8a64a))

## [1.19.2](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.19.1...v1.19.2) (2026-02-10)


### Bug Fixes

* **text_utils:** improve llm response parsing ([d0904bb](https://github.com/Web3-Plurality/plurality-ai-service/commit/d0904bbe08224906e523cfa08548969c2e31e73d))

## [1.19.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.19.0...v1.19.1) (2026-01-12)


### Bug Fixes

* Add custom .doc and .odt loaders with fallbacks ([0ade80d](https://github.com/Web3-Plurality/plurality-ai-service/commit/0ade80d102920686cc9869a510f04a746890c584))

# [1.19.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.18.0...v1.19.0) (2026-01-12)


### Features

* Add dependencies for extended document processing capabilities ([8ebcc8c](https://github.com/Web3-Plurality/plurality-ai-service/commit/8ebcc8cf88d93372f5d7c1809e7fe734161e9b9f))

# [1.18.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.17.1...v1.18.0) (2026-01-12)


### Features

* Add early validation for empty file uploads ([7a9dd84](https://github.com/Web3-Plurality/plurality-ai-service/commit/7a9dd84e75475eb76f14441135f5086558815176))
* Add system and Python dependencies for extended file types ([8d29e7a](https://github.com/Web3-Plurality/plurality-ai-service/commit/8d29e7a83d0715088ee6399b04b167d41387f1e4))
* Extend supported document types and update README ([b0c3da6](https://github.com/Web3-Plurality/plurality-ai-service/commit/b0c3da6a1c417ec37914229fbbb1931c58ee7034))
* Implement strategic document sampling for context generation ([266af6c](https://github.com/Web3-Plurality/plurality-ai-service/commit/266af6cc7dd51dd4a887705a69efe2f50f59d8f3))

## [1.17.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.17.0...v1.17.1) (2025-12-26)


### Bug Fixes

* Remove verbose debug print statements from web search ([0e85cb5](https://github.com/Web3-Plurality/plurality-ai-service/commit/0e85cb56f72596b682ad82bdfb52acc210562747))

# [1.17.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.16.1...v1.17.0) (2025-12-25)


### Features

* Add AWS Bedrock POC for multiple agents ([89ba36a](https://github.com/Web3-Plurality/plurality-ai-service/commit/89ba36af17073f920a0a7c2b6991167b46efa06b))
* **bedrock:** Add utility function for token estimation ([840276d](https://github.com/Web3-Plurality/plurality-ai-service/commit/840276d2650c8ee315ea8a26ed5f34e897efd980))
* **bedrock:** Implement token usage extraction and estimation ([88990c1](https://github.com/Web3-Plurality/plurality-ai-service/commit/88990c1ddf0ec6c275f6c18f5696c084a49c1d1c))
* **bedrock:** Pass messages and system prompt to _parse_response ([f726911](https://github.com/Web3-Plurality/plurality-ai-service/commit/f726911a615ce5d471a017dd200957a55db24631))
* Enable dynamic LLM selection in Agentic Query Service ([7ee6733](https://github.com/Web3-Plurality/plurality-ai-service/commit/7ee6733bd0747cb1083f0b4228a4fdcea9f113ae))
* Implement LLM Factory for dynamic model selection ([59e9ac8](https://github.com/Web3-Plurality/plurality-ai-service/commit/59e9ac805650804e5a6f8dda46460dcfa899d438))
* Integrate Google Custom Search API ([5703c60](https://github.com/Web3-Plurality/plurality-ai-service/commit/5703c60c6da00f2eff10fde762b7377c023eb181))
* Introduce AWS Bedrock model registry and service ([caa31cd](https://github.com/Web3-Plurality/plurality-ai-service/commit/caa31cd02d9a2323135e66f4ab03aa1b9623eec7))
* Remove AWS Bedrock Agents POC files ([68a0529](https://github.com/Web3-Plurality/plurality-ai-service/commit/68a0529c37d4fca3314391b3a7f849dbe8d6779f))

## [1.16.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.16.0...v1.16.1) (2025-12-22)


### Bug Fixes

* Add `jq` and `docx2txt` to requirements ([340983b](https://github.com/Web3-Plurality/plurality-ai-service/commit/340983b3d6dcdc2cf49b6ce88f7e39ab2f27f4ea))
* Enhance JSON loader with `jq` dependency check and logging ([f38fdef](https://github.com/Web3-Plurality/plurality-ai-service/commit/f38fdef02c9408767e62354a91a41a3160023fef))

# [1.16.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.15.0...v1.16.0) (2025-12-22)


### Features

* Add AI_SERVICE_API_KEY to .env.example ([765472a](https://github.com/Web3-Plurality/plurality-ai-service/commit/765472ac5d96161114a02f6ea9266a0d29c560f7))
* Add contextId to request schemas and vectorIds to response schemas ([979e65d](https://github.com/Web3-Plurality/plurality-ai-service/commit/979e65d224fdf94c1beb5f46df4e5f475eed737b))
* **api:** Pass contextId to upload_file endpoint ([9e7424e](https://github.com/Web3-Plurality/plurality-ai-service/commit/9e7424e75f68fc95e1c6a2a726100ed261f61484))
* **context:** Introduce webhook notification utility ([07afcfd](https://github.com/Web3-Plurality/plurality-ai-service/commit/07afcfd1ef4e4c7d8b9360237e02aaee92fae0e9))

# [1.15.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.14.1...v1.15.0) (2025-12-13)


### Features

* Adds Prometheus metrics service and helpers ([572fff5](https://github.com/Web3-Plurality/plurality-ai-service/commit/572fff566c305c73ae74b0ed52fd8bd919a3a0d6))

## [1.14.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.14.0...v1.14.1) (2025-12-13)


### Bug Fixes

* Replaces multi-stage Dockerfile with single-stage build ([7dd3e6a](https://github.com/Web3-Plurality/plurality-ai-service/commit/7dd3e6ab3e43c2c6c02824f72b6b0e76df55178f))

# [1.14.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.13.0...v1.14.0) (2025-12-13)


### Features

* **deps:** Add Prometheus client and FastAPI monitoring dependencies ([6ef8815](https://github.com/Web3-Plurality/plurality-ai-service/commit/6ef8815534ba7448a5474a048a766de571892d87))
* **monitoring:** Implement custom Prometheus HTTP metrics middleware ([194a856](https://github.com/Web3-Plurality/plurality-ai-service/commit/194a856c6300d38d9b3a755c7a6cf58547855101))
* **monitoring:** Integrate Prometheus metrics endpoint in FastAPI ([b3dec1e](https://github.com/Web3-Plurality/plurality-ai-service/commit/b3dec1eae902c201c097fbab5c11eebfde035d48))

# [1.13.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.12.0...v1.13.0) (2025-12-11)


### Features

* Add critical prompt review instruction to RAG service ([4e90baf](https://github.com/Web3-Plurality/plurality-ai-service/commit/4e90baf547cb40c9dd108a01b862a8ccbbc3b9c8))
* **agentic-rag:** Apply orphaned vector filtering in AgenticRAGService ([408e89e](https://github.com/Web3-Plurality/plurality-ai-service/commit/408e89e110ca9672293d94a1386dcddef4e66546))
* **context:** Implement and apply orphaned vector filtering in ContextService ([a297aca](https://github.com/Web3-Plurality/plurality-ai-service/commit/a297aca948e23ad93a250a323e9170ff4976e7ed))
* **context:** Optimize vector deletion using stored database IDs ([6aa0654](https://github.com/Web3-Plurality/plurality-ai-service/commit/6aa065497ba8e3cd60e969a8a8f3a9aa1d68dcd0))
* **context:** Store vector IDs in database during context creation ([2a35512](https://github.com/Web3-Plurality/plurality-ai-service/commit/2a3551271598b82fc35745eccabda6439f2ae297))
* **db:** Add batch context existence check ([700da13](https://github.com/Web3-Plurality/plurality-ai-service/commit/700da13213a76165b73e188524ee212991bc8a42))
* **db:** Introduce vector ID storage and retrieval functions ([57874ac](https://github.com/Web3-Plurality/plurality-ai-service/commit/57874ac1c0c092310999eeee49450632aa127924))
* **rag:** Introduce `should_show_context` for RAG state ([4a1379c](https://github.com/Web3-Plurality/plurality-ai-service/commit/4a1379c06977e8b7ad4beb1313b0073e11006c50))
* **vector:** Implement and apply orphaned vector filtering in VectorService ([c3dd736](https://github.com/Web3-Plurality/plurality-ai-service/commit/c3dd7365758e92336b80b4e78f8a7a016403c0f0))

# [1.12.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.11.3...v1.12.0) (2025-12-07)


### Features

* **agentic_query:** Use Gemini 3 for agentic queries and tool binding ([4eb99cd](https://github.com/Web3-Plurality/plurality-ai-service/commit/4eb99cd8057d24d803a688d46ca764e392cafae4))
* Introduce Gemini 3 Pro LLM with thought signatures ([80b0389](https://github.com/Web3-Plurality/plurality-ai-service/commit/80b0389237cb65eed6765f8e22d474c3c87fd72c))
* Update dependencies and refactor langchain_text_splitters import paths ([e2c6356](https://github.com/Web3-Plurality/plurality-ai-service/commit/e2c6356e4ea2b0af18ee1c8f7576949bdb74a46e))

## [1.11.3](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.11.2...v1.11.3) (2025-12-06)


### Bug Fixes

* Implements asynchronous text embedding ([9fc6f62](https://github.com/Web3-Plurality/plurality-ai-service/commit/9fc6f621dcce8d4dbf7d64621aca157ee1c3dddb))

## [1.11.2](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.11.1...v1.11.2) (2025-12-05)


### Bug Fixes

* Uses asyncio task for background processing ([7fa7ce9](https://github.com/Web3-Plurality/plurality-ai-service/commit/7fa7ce9e2cbbfdc798e335876fc07d716ab64306))

## [1.11.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.11.0...v1.11.1) (2025-11-28)


### Bug Fixes

* Adds manual GHCR prod promotion workflow with verification ([af767f3](https://github.com/Web3-Plurality/plurality-ai-service/commit/af767f305a4775b5d7c0b5a2676213b97e028db4))

# [1.11.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.10.0...v1.11.0) (2025-11-28)


### Bug Fixes

* Enhance URL validation regex ([1753a01](https://github.com/Web3-Plurality/plurality-ai-service/commit/1753a01e1930529056b09a1eb4354fec2dc90d7d))


### Features

* Improve LLM data separation and fidelity ([28150cc](https://github.com/Web3-Plurality/plurality-ai-service/commit/28150ccaac4a480a29cdb7546c8e85f553c1f4ad))
* **llm:** Increase max_output_tokens and document temperature for Pluto's persona ([3156c2b](https://github.com/Web3-Plurality/plurality-ai-service/commit/3156c2b80e6fa6d13d6ca01e2da23f6ae9842502))

# [1.10.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.9.0...v1.10.0) (2025-11-25)


### Features

* Ensures correct message sequencing for Gemini ([a968041](https://github.com/Web3-Plurality/plurality-ai-service/commit/a968041d966c89e0549723daf61bb32e2d14c748))
* Improves prompt generation for chat agent optimization ([d88af91](https://github.com/Web3-Plurality/plurality-ai-service/commit/d88af9168c5da0bea67b110d000762c0a41161b3))

# [1.9.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.8.0...v1.9.0) (2025-11-20)


### Bug Fixes

* agent name change from plu to pluto ([8b9537a](https://github.com/Web3-Plurality/plurality-ai-service/commit/8b9537a7d06a759c37c7fee558e326ad0920ab07))
* create separate utils for utils functions ([e61c112](https://github.com/Web3-Plurality/plurality-ai-service/commit/e61c112d797f75a2013f98081bf97b9a112a5e44))
* Improves context relevance check and prompt optimization ([ec25d0a](https://github.com/Web3-Plurality/plurality-ai-service/commit/ec25d0ab09896423782777eeeb8f6ad849061e99))
* relevent context check ([b6d8882](https://github.com/Web3-Plurality/plurality-ai-service/commit/b6d8882aaff91a52ee32f45e2309467cd6412b46))
* remove system prompts to keep responses simple ([49dfae5](https://github.com/Web3-Plurality/plurality-ai-service/commit/49dfae508928622e897813c473542eacfd77834a))


### Features

* add  plu agent branch for query ([b13199d](https://github.com/Web3-Plurality/plurality-ai-service/commit/b13199d21c5d0dcd489ff5dbed0472804a8452d3))
* Add /agentic-rag-query endpoint and update legacy doc ([04934cf](https://github.com/Web3-Plurality/plurality-ai-service/commit/04934cf6fbc936b8d3b6f5fd840a33100bde18eb))
* add chat hostory in check relevance ([15cb43b](https://github.com/Web3-Plurality/plurality-ai-service/commit/15cb43baf753a8f09b935929e4a86294970941e7))
* Add LangGraph dependency for agentic RAG ([51d255c](https://github.com/Web3-Plurality/plurality-ai-service/commit/51d255cf1c64a689b1e04f1ed3d5b458876b9426))
* add system prompt ([b9890d7](https://github.com/Web3-Plurality/plurality-ai-service/commit/b9890d775c1e734f9e26df558bebd129d1030275))
* Implement core Agentic RAG service with LangGraph ([19fa300](https://github.com/Web3-Plurality/plurality-ai-service/commit/19fa300937ec04d34cfa75af2cd48849e21cdfbb))
* Integrate Agentic RAG service into ContextService ([bfd949e](https://github.com/Web3-Plurality/plurality-ai-service/commit/bfd949e03d886b68c9dad28e85d958adf9fd045a))
* make plu prompt  response as user answer ([2f169a4](https://github.com/Web3-Plurality/plurality-ai-service/commit/2f169a4ba570cd9cbadd9828d631bb3eaf28ff81))
* use gemini 2.5 model in chat config ([f0c3ffe](https://github.com/Web3-Plurality/plurality-ai-service/commit/f0c3ffe204f19e1cd4801f79329ccd499f373347))

# [1.8.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.7.1...v1.8.0) (2025-11-08)


### Bug Fixes

* add await in ainvoke method ([cecd48e](https://github.com/Web3-Plurality/plurality-ai-service/commit/cecd48eb82cd34c51e2355a9565dd6099a215c4c))


### Features

* add follow up mechanism with chat history ([0fb1a6b](https://github.com/Web3-Plurality/plurality-ai-service/commit/0fb1a6bffadc725535798034c119a3723e52c7fe))
* add platforms ([7e2813d](https://github.com/Web3-Plurality/plurality-ai-service/commit/7e2813dea6ecdcf3398c8cda528a769376aa7f00))
* comment out topic-based chat history optimization ([f825dc5](https://github.com/Web3-Plurality/plurality-ai-service/commit/f825dc5b51dfff616605f838512741c4109659cd))
* Enhance insight extraction with specific user data points ([85c482f](https://github.com/Web3-Plurality/plurality-ai-service/commit/85c482fc71954c4fead548e2c2f4e68cf9983570))
* Implements byte-aware chunking to save maximum content in a chunk ([dca2ec0](https://github.com/Web3-Plurality/plurality-ai-service/commit/dca2ec0a5ae18121378ebceefbe79804cd11b03f))
* Improve chunking and context handling ([95e7616](https://github.com/Web3-Plurality/plurality-ai-service/commit/95e76169a9a4d454037f63d52c41a765406caaf1))
* optimize chat history ([ab6d97c](https://github.com/Web3-Plurality/plurality-ai-service/commit/ab6d97c873bc608417c08bbb31d4e870c951e11a))
* optimize chat history in extensiion response ([e410073](https://github.com/Web3-Plurality/plurality-ai-service/commit/e4100739b7fae36832852ec314447fd4bec09722))
* Temporarily comment out topic-based chat history optimization ([a3bbd5c](https://github.com/Web3-Plurality/plurality-ai-service/commit/a3bbd5c68961cbd9b90a198d218c8b95a264b956))

## [1.7.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.7.0...v1.7.1) (2025-10-15)


### Bug Fixes

* update gemini 2.0 model ([b8aafc4](https://github.com/Web3-Plurality/plurality-ai-service/commit/b8aafc4890614dfb92abef6e13e8233c4ad0d85b))

# [1.7.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.6.0...v1.7.0) (2025-10-14)


### Features

* add context and profile delete api ([bdbf1db](https://github.com/Web3-Plurality/plurality-ai-service/commit/bdbf1dbcb6bb2c73817e4bacc86d25b803e2144e))

# [1.6.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.5.0...v1.6.0) (2025-09-23)


### Bug Fixes

* add space in messages ([dd09b76](https://github.com/Web3-Plurality/plurality-ai-service/commit/dd09b760f93b05899d2b22a6d6c1080f96ee08a4))


### Features

* update requirements.txt ([626a718](https://github.com/Web3-Plurality/plurality-ai-service/commit/626a718e4727940b59293f4541a4934412d7da3a))

# [1.5.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.4.1...v1.5.0) (2025-09-19)


### Bug Fixes

* add attached context ([15d5517](https://github.com/Web3-Plurality/plurality-ai-service/commit/15d55177698dd8e3c9da6acca43baf95c734cbfa))
* add problem and get problem of context fixed ([b152b7a](https://github.com/Web3-Plurality/plurality-ai-service/commit/b152b7abd9c66bf8ec8f10aaf76e4075cf19911c))
* remove context in followup chat ([b978026](https://github.com/Web3-Plurality/plurality-ai-service/commit/b9780265b4fb037d1f0ad272cb8d14e58e38b5b1))
* update context_service.py ([c177758](https://github.com/Web3-Plurality/plurality-ai-service/commit/c177758cc625aacfddda97141ed8b5a6443f6ef2))


### Features

* add context in optmize prompt ([5d84fae](https://github.com/Web3-Plurality/plurality-ai-service/commit/5d84fae03021271b48f79f3b2cd9f785bc28ac2c))
* update context fetching logic and some improvements ([e2f1148](https://github.com/Web3-Plurality/plurality-ai-service/commit/e2f1148984727d0f710052608a43aa75829e71a8))

## [1.4.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.4.0...v1.4.1) (2025-09-14)


### Bug Fixes

* optimize prompt to fix chat history problem ([0a367f6](https://github.com/Web3-Plurality/plurality-ai-service/commit/0a367f69b93dac6de38fa67f67e151bea1a8005e))
* testing differnt prompt ([ac04776](https://github.com/Web3-Plurality/plurality-ai-service/commit/ac04776eb73bac127a2d2258270333303a6ae0b1))

# [1.4.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.3.2...v1.4.0) (2025-09-04)


### Bug Fixes

* improve formatting of the optimized reponse ([c5a5cd9](https://github.com/Web3-Plurality/plurality-ai-service/commit/c5a5cd916bf25d538b6cb65ab2b9cdc54985af89))


### Features

* add query data separation function ([2eb0633](https://github.com/Web3-Plurality/plurality-ai-service/commit/2eb0633f8a1a83c4484748ae1d986d426bdd5f42))

## [1.3.2](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.3.1...v1.3.2) (2025-09-01)


### Bug Fixes

* update dockerfile for startup ([45bbb8e](https://github.com/Web3-Plurality/plurality-ai-service/commit/45bbb8e50594ef1cd833f2528dd4efd64e7a8a52))

## [1.3.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.3.0...v1.3.1) (2025-09-01)


### Bug Fixes

* docker build issue ([2fa0de2](https://github.com/Web3-Plurality/plurality-ai-service/commit/2fa0de29f2aa2c2f8d900b532ae47258d90d559d))

# [1.3.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.2.2...v1.3.0) (2025-09-01)


### Bug Fixes

* bug in chat api and add .env.example ([6f61ae7](https://github.com/Web3-Plurality/plurality-ai-service/commit/6f61ae7b6e7a84d2f07f96aa0ac9aa346cd8fa7b))
* clean the query code ([08cb946](https://github.com/Web3-Plurality/plurality-ai-service/commit/08cb94601c48e319b4a82e3c958a23eb67c99496))
* optimized the query ([00ce478](https://github.com/Web3-Plurality/plurality-ai-service/commit/00ce478aaa73fdf82e4e6b4cdcae869a8151f6f1))
* remove profileId from prompt ([7799c1f](https://github.com/Web3-Plurality/plurality-ai-service/commit/7799c1f7a4d70973e7c43b6455667a6b44c4de9d))
* resolve nltk download problme ([c4a9eda](https://github.com/Web3-Plurality/plurality-ai-service/commit/c4a9eda0d9d72e486b81c18335ea1d52fedb70c7))
* title lengeht of context should be not more than 3 ([3053bb1](https://github.com/Web3-Plurality/plurality-ai-service/commit/3053bb146e63d74b5dbf7c3d5a96b0140c6d0134))
* token extraction ([f6ccd5c](https://github.com/Web3-Plurality/plurality-ai-service/commit/f6ccd5cc95b6d86d91c88eccdeb898980082ed6a))


### Features

* add chunking ([1a8294d](https://github.com/Web3-Plurality/plurality-ai-service/commit/1a8294d6bf46a5ca6a7a745e832a96386f8e67da))
* add pdf ([34953a0](https://github.com/Web3-Plurality/plurality-ai-service/commit/34953a031ff6030560d7ac71e7de5395034eca6a))
* add rag api ([dc4ae17](https://github.com/Web3-Plurality/plurality-ai-service/commit/dc4ae17be64e66029487af63dc734ecd9a4a52a0))
* add rag endpoint and refactored the code ([f389e9c](https://github.com/Web3-Plurality/plurality-ai-service/commit/f389e9c2e3e5581ffe3d0f6411f810950e3f2e12))
* add rate limit to query ([ab2f5ce](https://github.com/Web3-Plurality/plurality-ai-service/commit/ab2f5ce817d4afb3f0191f71e51578acfb2a76a5))
* create optimize prompt from rag query ([0ea5978](https://github.com/Web3-Plurality/plurality-ai-service/commit/0ea59785c40c0e0f8036072d5820d6e05724dccb))
* integerate get context  api ([2e150c1](https://github.com/Web3-Plurality/plurality-ai-service/commit/2e150c1c00a7fa3572a7a98ebe234a515e9e68c2))
* integrate multi-threading ([acedd18](https://github.com/Web3-Plurality/plurality-ai-service/commit/acedd18bc1ee71fd548a85c7357e6f3fe3615795))
* update context_routes.py ([c36810e](https://github.com/Web3-Plurality/plurality-ai-service/commit/c36810edbd09c7bb531b53d07186c1411df98763))
* update main.py path and update dependencies ([783bdad](https://github.com/Web3-Plurality/plurality-ai-service/commit/783bdadcc08c49d95b565b08944fe97758495e6a))

## [1.2.2](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.2.1...v1.2.2) (2025-08-08)


### Bug Fixes

* revert flow changes and bugfix ([cf0ce41](https://github.com/Web3-Plurality/plurality-ai-service/commit/cf0ce414e3d472498c52112f9e295d40b016b557))

## [1.2.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.2.0...v1.2.1) (2025-08-08)


### Bug Fixes

* bug fixes and query flow improvements ([cc54494](https://github.com/Web3-Plurality/plurality-ai-service/commit/cc544942e6cb7ae0201608890ef411f5a648b091))

# [1.2.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.1.7...v1.2.0) (2025-08-03)


### Features

* add enabled tools prompt engineering to enabled and disabled tools ([79ba184](https://github.com/Web3-Plurality/plurality-ai-service/commit/79ba184536e06ad5daab2e438b7fcaca67017ea6))
* add similarity search condition ([e37676c](https://github.com/Web3-Plurality/plurality-ai-service/commit/e37676c84bf28bbe293d658a97fce1ec0ae4275e))
* implement the filters of tooling ([e8a3818](https://github.com/Web3-Plurality/plurality-ai-service/commit/e8a3818ebc887a0c95791d53296eefceb4bd7806))
* implement Vague Query flow ([335f101](https://github.com/Web3-Plurality/plurality-ai-service/commit/335f101ad9b7161498ca86b19f315298d75ce6d0))
* update context_service.py ([5f121ca](https://github.com/Web3-Plurality/plurality-ai-service/commit/5f121ca5308be032de51dc97a723a6e740816794))

## [1.1.7](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.1.6...v1.1.7) (2025-07-28)


### Bug Fixes

* comment extra imports in main.py ([3fc874b](https://github.com/Web3-Plurality/plurality-ai-service/commit/3fc874b31cab3052ae4c9bb80bba742b1e49a243))

## [1.1.6](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.1.5...v1.1.6) (2025-07-26)


### Bug Fixes

* release version in ci ([e76c0b7](https://github.com/Web3-Plurality/plurality-ai-service/commit/e76c0b73c1191db4f09a347c11573ff2f3845d9b))

## [1.1.5](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.1.4...v1.1.5) (2025-07-26)


### Bug Fixes

* release version in prod ci ([7b5de7a](https://github.com/Web3-Plurality/plurality-ai-service/commit/7b5de7acef8a8c186012434724679ddee7324b95))

## [1.1.4](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.1.3...v1.1.4) (2025-07-26)


### Bug Fixes

* release version in prod ci ([363b967](https://github.com/Web3-Plurality/plurality-ai-service/commit/363b967c07ef14aac18aa1d1eaaea08aad1e78b8))

## [1.1.3](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.1.2...v1.1.3) (2025-07-26)


### Bug Fixes

* release version in ci ([98d1cbd](https://github.com/Web3-Plurality/plurality-ai-service/commit/98d1cbd60b047c2e2919d3a5ec23603a864dc94e))

## [1.1.2](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.1.1...v1.1.2) (2025-07-26)


### Bug Fixes

* release version in ci ([f4eea87](https://github.com/Web3-Plurality/plurality-ai-service/commit/f4eea87794f0c0201ef7682d53cf2db2fdd77c09))

## [1.1.1](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.1.0...v1.1.1) (2025-07-25)


### Bug Fixes

* release version in ci ([d2df8da](https://github.com/Web3-Plurality/plurality-ai-service/commit/d2df8da1ecf507343a464c8a8aba34d99082d34d))

# [1.1.0](https://github.com/Web3-Plurality/plurality-ai-service/compare/v1.0.0...v1.1.0) (2025-07-25)


### Features

* add production ci pipeline ([d146993](https://github.com/Web3-Plurality/plurality-ai-service/commit/d146993bb587fd633e81804a5a5639af9895b703))

# 1.0.0 (2025-07-25)


### Bug Fixes

* add env example ([d95c13f](https://github.com/Web3-Plurality/plurality-ai-service/commit/d95c13fd964dc9bef1b3613a2d4b79b9398bfb37))
* add semantic release dependency ([3ae6522](https://github.com/Web3-Plurality/plurality-ai-service/commit/3ae6522837fbc3e17aad28a0a51470ae4e2ca69f))


### Features

* add ci pipeline ([6990ab3](https://github.com/Web3-Plurality/plurality-ai-service/commit/6990ab3d2413801d0c664f16ff53944a3853603e))
* add context url ([118bd11](https://github.com/Web3-Plurality/plurality-ai-service/commit/118bd11f5495344cfed4e1e1e598545686edb97f))
* add custom rag implementation ([d587de8](https://github.com/Web3-Plurality/plurality-ai-service/commit/d587de89a84d1d856e3ce604f0fd8b3c1a5afb49))
* add description in the context ([759c627](https://github.com/Web3-Plurality/plurality-ai-service/commit/759c6279228b4038c5ace87a6266d62ffeb0073e))
* add json ([90a23ef](https://github.com/Web3-Plurality/plurality-ai-service/commit/90a23ef3fee1830d14ec4a272802be9d38881bd6))
* add pdf and markdown ([0b580b7](https://github.com/Web3-Plurality/plurality-ai-service/commit/0b580b71b455e8390b45905047677afd0b067162))
* add reddit api ([167203e](https://github.com/Web3-Plurality/plurality-ai-service/commit/167203eaa880809f0be993d8026242e4adbf053a))
* add spotify ([45e8402](https://github.com/Web3-Plurality/plurality-ai-service/commit/45e840277f5893d979c3170de3d2fd752a8d0588))
* add suggested prompt from profile name ([0efb909](https://github.com/Web3-Plurality/plurality-ai-service/commit/0efb909c72bcd197a4d2f0136b68396ae383608b))
* add tiktok data api ([2780152](https://github.com/Web3-Plurality/plurality-ai-service/commit/27801528b6d3a04436840b6ac5018b963790bab7))
* add twitter api ([0951896](https://github.com/Web3-Plurality/plurality-ai-service/commit/09518965742f9e26c1396e831c57743fc6a6d541))
* create docker file ([917ab72](https://github.com/Web3-Plurality/plurality-ai-service/commit/917ab72cc714d09c5fd4b8671e064cc150233e56))
* create fast api for rag ([c00aac2](https://github.com/Web3-Plurality/plurality-ai-service/commit/c00aac2a9d344dc6782644e3682220ce4a37ab07))
* integrartte chat history ([c7a8af5](https://github.com/Web3-Plurality/plurality-ai-service/commit/c7a8af5fbaf5301459e5af8dcbd3245b4bf54357))
* integrate s3 bucket inplacce of pinecone ([cf454d0](https://github.com/Web3-Plurality/plurality-ai-service/commit/cf454d01bf2fb7dc30f761b5ac9a1177ac939f96))
* integrate web search tooling in Rag ([15ee76c](https://github.com/Web3-Plurality/plurality-ai-service/commit/15ee76c2ee960340c8497119cfcfc4d8bfd42fc8))
* update context_service.py ([e9a7a22](https://github.com/Web3-Plurality/plurality-ai-service/commit/e9a7a22596f4191e9e19ae35402642f0d4e417e6))

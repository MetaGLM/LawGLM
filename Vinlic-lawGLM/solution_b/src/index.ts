import minimist from 'minimist';

import "@/lib/initialize.ts";
import server from "@/lib/server.ts";
import question from '@/lib/question.ts';
import routes from '@/api/routes/index.ts';
import logger from '@/lib/logger.ts';

// 获取命令行参数
const cmdArgs = minimist(process.argv.slice(2));
const startupTime = performance.now();

(async () => {
    const param = cmdArgs.q;
    if(param) {
        if(param.trim() == 'all')
            await question.generateQuestionsAnswer();
        else
            await question.generateQuestionAnswer(param);
        process.exit(0);
    }
    
    logger.header();

    logger.info("<<<< law qa server >>>>");
    logger.info("Process id:", process.pid);

    server.attachRoutes(routes);
    await server.listen();
    
})()
    .then(() =>
        logger.success(
        `Service startup completed (${Math.floor(performance.now() - startupTime)}ms)`
        )
    )
    .catch(err => logger.error(err));
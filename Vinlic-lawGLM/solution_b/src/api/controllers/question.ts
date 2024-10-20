import { PassThrough } from "stream";
import question from "@/lib/question.ts";
import logger from "@/lib/logger.ts";

async function generateQuestionAnswerStream(query: string) {
    const transStream = new PassThrough();
    question.generateQuestionAnswer(query, msg => {
        // console.log(msg);
        transStream.write(`${JSON.stringify(msg)}\n\n`);
    })
        .then(() => {
            transStream.end();
        })
        .catch(err => {
            logger.error(err);
            transStream.end();
        });
    return transStream;
}

export default {
    generateQuestionAnswerStream
}
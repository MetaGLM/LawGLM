import _ from "lodash";

import Request from "@/lib/request/Request.ts";
import Response from "@/lib/response/Response.ts";
import question from "@/api/controllers/question.ts";

export default {
  prefix: "/question",

  post: {
  
    "/generate_answer": async (request: Request) => {
      request
        .validate('body.query');
      const { query } = request.body;
      const stream = await question.generateQuestionAnswerStream(query);
      return new Response(stream, {
        type: "text/event-stream"
      });
    }

  },
};
